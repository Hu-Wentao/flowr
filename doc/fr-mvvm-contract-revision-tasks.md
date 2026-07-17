# fr-mvvm-contract 修订任务清单

## 目的

为 `fr-mvvm-contract` 技能整理一份可持续更新的修订任务列表。
本阶段只记录任务、范围、验收点与待确认项，后续对话再逐步细化并执行重构。

## 目标范围

- `skills/fr-mvvm-contract/SKILL.md`
- `skills/fr-mvvm-contract/scripts/page_context.py`
- `skills/fr-mvvm-contract/scripts/new_page.py`
- 可能联动:
  - `skills/README.md`
  - `skills/fr-mvvm-contract/references/fr-acdd.md`
  - `skills/fr-mvvm-contract/references/fr-acdd-install.md`

## 已确认修订目标

### 1. 输入门禁

- 明确输入必填参数为:
  - `figmaUrl`
  - `api`
- `api` 仅允许以下三种形态:
  - `NONE`
    - 代表页面没有 API、当前不需要 API、或暂时为空
  - `BFF`
    - 代表由 AI 自行定义该页面需要的 API、Req、Resp，并完成页面 API 拆分分析
  - `<有效API地址>`
    - 代表提供了真实可读的 API 地址，后续需要读取并分析接口定义

### 2. 前置分析

- 生成前必须先读:
  - Figma 配置
  - 邻近页面
  - 邻近组件
  - theme 约束
- 生成前必须处理 API 配置:
  - `api = NONE`
    - 跳过 API 读取，但仍需在分析结果中明确该页面无 API 依赖
  - `api = BFF`
    - 开始页面 API 拆分
    - 分析页面需要的 Req/Resp
    - 明确是否存在多上游接口聚合、首屏加载、分 tab 懒加载、分页、刷新等模式
  - `api = <有效API地址>`
    - 读取 API 定义
    - 分析 endpoint、参数、响应、空态、错误态、加载态

### 3. 页面生成

- 不再生成单独的数值定义类，例如:

```dart
class _NotificationsPageDimens {
  static const double PAGE_HORIZONTAL_PADDING = 12;
  static const double PANEL_TOP_RADIUS = 16;
}
```

- UI 中直接使用数值即可。
- 但不能机械照搬 Figma 的固定像素值。
- 需要优先根据实际布局语义使用更合适的约束表达，例如:
  - 占据可用宽度
  - `Expanded` / `Flexible`
  - 基于父布局约束自适应
  - 仅在确有必要时使用固定数值

### 4. 事实源与派生策略

- `contract dart` 是唯一长期事实源。
- AI 的临时分析不落盘为仓库文件。
- 如果现有生成器暂时仍需要 JSON 输入，则该 JSON 只允许作为一次性临时中转，不得作为长期设计稿入库。
- 开发者后续若手动修改 `contract dart`，AI 需要以修正后的 `contract dart` 为准，同步修正其他相关文件。
- `proto/json5` 必须由 `contract dart` 通过脚本稳定派生，不允许手工维护为并行事实源。
- `BFF` 模式下必须显式考虑 `fr_acdd` 注解设计，至少覆盖:
  - `@FrAcddPage`
  - `@FrAcddDto`
  - `@FrAcddField(tag: ...)`
  - `@FrAcddFreezed`
  - `Figma` / `API` / `Route` 注释的稳定可提取性

### 5. DTO 与本地状态边界

- `DTO` 只表示后端可传输、可派生为 `proto/json5` 的数据结构。
- 页面本地状态不属于 `DTO` 语义，不应作为 `FrAcddDtoKind` 的一部分长期鼓励使用。
- AI 首轮根据 UI 推断出的字段归属只是假设，开发者可以在 `contract dart` 中手动调整:
  - 哪些字段属于页面本地状态
  - 哪些字段属于后端返回 DTO
- 后续 AI 和脚本都必须以修正后的 `contract dart` 为准。
- 本地状态与后端 DTO 的纠偏，应该通过调整类边界和字段归属来完成，而不是把“状态字段”继续混入可导出 DTO 中。

### 6. FrAcddMode 与导出格式边界

- `FrAcddMode` 只表达 contract 的语义模式。
- 当前仅保留两类模式:
  - `api`
  - `bff`
- `proto` 和 `json5` 只是从 `contract dart` 派生时选择的输出格式，不属于 contract mode。
- 因此不应在 `contract dart` 中定义“proto 模式”或“json 模式”之类概念。
- 导出格式选择应只存在于脚本/CLI 层，例如 `--format proto` 或 `--format json5`。

### 7. BFF 的 API 注释模板与导出参数

- `BFF` 模式下，contract 注释中的 `BFF-API:` 段落应放在 `Models:` 段落之后。
- `BFF-API:` 段落使用固定多行模板，每个上游接口一个 block，例如:

```dart
/// BFF-API:
/// - GET <BASE>/home-page/summary
///   [HomePortfolioSummaryReq], [HomePortfolioSummaryModel]
/// - GET <BASE>/home-page/recommendations
///   [HomeStockRecommendationReq], [HomeStockRecommendationModel]
```

- `BFF-API` 的 `<BASE>/...` 路径由 contract 文件路径稳定派生，下划线 `_` 统一转为连字符 `-`。
- 顶级页面示例:
  - `lib/page/home_page/home_page.dart` -> `<BASE>/home-page/...`
- 子页面示例:
  - `lib/page/home_page/sub_page/sub_page.dart` -> `<BASE>/home-page/sub-page/...`
- 技能 spec 允许新增可选参数 `exportFormat`:
  - `JSON`
  - `PROTO`
- `exportFormat` 默认值为 `JSON`。
- 当 `exportFormat = JSON` 时，实际派生产物为 `.md` 文档，用于承载多 API 的 JSON5 请求/响应片段。
- 当 `exportFormat = PROTO` 时，派生产物继续为 `.proto`，并支持多 API + req/rsp 声明。
- 当 `exportFormat = JSON` 时，不要求字段手写 `@FrAcddField(tag: ...)`。
- 如果字段注解只是空的 `@FrAcddField()`，则应直接省略该注解。
- `api` 还允许使用快捷写法:
  - `BFF-JSON`
    - 等价于 `api = BFF` 且 `exportFormat = JSON`
  - `BFF-PROTO`
    - 等价于 `api = BFF` 且 `exportFormat = PROTO`

## 任务列表

### A. 技能文档修订

- [x] A1. 更新 `SKILL.md` 的输入门禁说明
  - 明确 `figmaUrl` 与 `api` 为必填输入
  - 明确 `api` 的三种合法取值与语义
  - 明确缺少输入时不能直接生成页面

- [x] A2. 更新 `SKILL.md` 的前置分析流程
  - 先读 Figma
  - 再读邻近页面、组件、theme 约束
  - 最后按 `api` 取值进入不同分析分支

- [x] A3. 更新 `SKILL.md` 的页面生成规则
  - 删除“单独数值定义类”相关生成约定
  - 增加“固定值与响应式约束的取舍原则”

- [x] A4. 更新 `SKILL.md` 的事实源规则
  - 明确 `contract dart` 是唯一长期事实源
  - 明确 AI 的分析过程不落盘为独立设计稿
  - 明确开发者修改 `contract dart` 后，其他文件应以其为准重新同步

- [x] A5. 更新 `SKILL.md` 的 DTO 边界规则
  - 明确 `DTO` 只描述后端数据契约
  - 明确页面本地状态不属于 `FrAcddDtoKind` 的推荐用法
  - 明确 AI 首轮字段归属只是候选，允许开发者在 `contract dart` 中重划边界

- [x] A6. 更新 `SKILL.md` 的 `FrAcddMode` 规则
  - 明确 `FrAcddMode` 只表达 `api` / `bff`
  - 明确 `proto/json5` 是派生输出格式，不是 contract mode

- [x] A7. 更新 `SKILL.md` 的 BFF API 模板规则
  - 明确 `BFF` 时 `BFF-API:` 需要放在 `Models:` 之后
  - 明确多行 `METHOD <BASE>/...` + `[Req], [Resp]` 模板
  - 明确 `<BASE>` 路径派生规则

- [x] A8. 更新 `SKILL.md` 的导出格式参数说明
  - 增加 `exportFormat`
  - 明确参数值为 `JSON` / `PROTO`
  - 明确 `JSON` 的实际产物是 `.md`
  - 明确该参数只在 `BFF` 下有效
  - 明确 `BFF-JSON` / `BFF-PROTO` 是 `api` 的快捷写法

### B. 上下文分析脚本修订

- [x] B1. 更新 `page_context.py` 的输出提示词
  - 明确要求先检查 `figmaUrl`
  - 明确要求先检查 `api`
  - 明确 `NONE`、`BFF`、`<有效API地址>` 三种分支行为

- [x] B2. 补充邻近页面/组件/theme 分析提示
  - 让上下文输出中显式包含这些约束

### C. 生成器修订

- [x] C1. 更新 `new_page.py` 的输入约束
  - 明确临时 spec 中对应字段是否必填
  - 明确 `api` 三种形态的处理策略
  - 明确临时 spec 只作为生成中转，不是长期事实源

- [x] C2. 更新生成代码的布局策略
  - 不再输出 `_XxxPageDimens` 之类的常量类
  - 直接在 UI 中使用数值
  - 保留对自适应布局的优先指导，不把 Figma 固定值直接绝对化

- [x] C3. 检查示例与模板
  - 避免示例代码继续引导出单独数值类
  - 如有必要，补一个 `NONE` / `BFF` / 有效 API 地址的示例

- [x] C4. 评估或补充“从 `contract dart` 回推同步其他产物”的能力
  - 明确 `.v.dart` / `.vm.dart` / `proto` / `json5` 的同步入口
  - 避免必须依赖长期保存的中间分析稿

- [x] C5. 更新示例导出物命名
  - `json5` 导出不再落为 `.json5`
  - 示例和文档统一改为 `.md`

### D. 文档联动修订

- [ ] D1. 检查 `skills/README.md` 是否需要同步更新
- [x] D2. 检查 `fr-acdd` 参考文档是否需要同步补充 `BFF` 输入门禁
- [x] D3. 检查 `fr-acdd` 参考文档是否需要明确“`proto/json5` 从 `contract dart` 稳定派生”的规则
- [ ] D4. 检查 `fr-acdd` 注解约束是否需要在技能文档中前置强调
  - `@FrAcddPage`
  - `@FrAcddDto`
  - `@FrAcddField(tag: ...)`
  - `@FrAcddFreezed`
  - 可提取的 `Figma` / `API` / `Route` 注释

- [x] D5. 评估 `FrAcddDtoKind` 的语义收缩方案
  - 将公开用法收缩为仅 `root` / `nested`
  - 删除 `state` / `ignored`
  - 同步清理提取器、测试、README 和示例

- [x] D6. 检查 `fr_acdd` 文档与 CLI 是否清晰区分“模式”和“格式”
  - `FrAcddMode` 仅为 `api` / `bff`
  - `--format` 仅为 `proto` / `json5`
  - 避免 README、测试名、注释中把模式和格式混写成同一层概念

- [x] D7. 检查 `fr_acdd` 文档是否明确 `BFF` 的 `BFF-API:` 注释模板
  - `BFF-API:` 位置在 `Models:` 之后
  - block 内需同时声明 method/path 与 req/rsp refs

### E. 验证与回归

- [x] E1. 文档验证
  - 确认 `SKILL.md`、README、参考文档之间的描述一致

- [ ] E2. 生成器冒烟验证
  - 用 `api = NONE` 生成一次
  - 用 `api = BFF` 生成一次
  - 用 `api = <有效API地址>` 的示例 spec 验证一次

- [x] E3. `fr_acdd` 派生验证
  - 从 `contract dart` 导出一次 `proto`
  - 从 `contract dart` 导出一次 `json5`
  - 确认 `fr_acdd` 注解和注释足以稳定产出

- [x] E4. 输出结构验证
  - 确认不再生成单独的尺寸常量类
  - 确认页面仍保持 contract / view / viewModel 分层
  - 确认生成结果没有引入隐藏兼容开关
  - 确认 `proto/json5` 不再作为人工维护文件参与事实源竞争

## 待确认细节

- [ ] `figmaUrl` 和 `api` 在临时 spec 中的字段名是否固定为这两个名字
- [ ] 若用户未提供 `figmaUrl` 或 `api`，是直接报错终止，还是输出待补全提示
- [ ] `api = <有效API地址>` 的“有效”判定标准
  - 仅 URL 格式合法
  - 还是必须可读取并可解析
- [ ] `api = NONE` 时，contract 注释中的 `API` 段落如何写
- [ ] `api = BFF` 时，contract 注释中的 `BFF-API` 段落是否需要固定模板
- [ ] “直接在 UI 中使用数值”是否允许局部 `const double` 变量
- [ ] 响应式布局的推荐手段是否要在技能中明确排序
- [ ] `contract dart` 中哪些注释与注解必须保持稳定格式，以便 `fr_acdd` 长期可靠派生
- [ ] 是否需要统一术语，将“BFF-PROTO / BFF-JSON”改写为“`bff` 模式的 `JSON/PROTO` 导出”

## 执行顺序建议

1. 先修订 `SKILL.md`，锁定规则。
2. 再修订 `page_context.py`，让分析提示与规则一致。
3. 再修订 `new_page.py`，落地到生成行为。
4. 再确认 `fr_acdd` 注解与导出约束。
5. 最后做 README / reference 联动和冒烟验证。

## 变更记录

- 2026-06-11: 初始化任务清单，录入首批修订目标，尚未开始实现。
- 2026-06-11: 确认 `contract dart` 为唯一长期事实源；AI 分析不落盘；`proto/json5` 必须通过脚本从 `contract dart` 稳定派生，并补充 `fr_acdd` 注解设计关注点。
- 2026-06-11: 确认 `DTO` 仅表示后端可传输数据；页面本地状态与 DTO 分离；开发者可通过修改 `contract dart` 重新划分字段归属。
- 2026-06-11: 确认 `FrAcddMode` 仅表示 `api` / `bff` 两类 contract 模式；`proto/json5` 仅为派生产物格式，不进入 contract 定义。
- 2026-06-11: 决定不保留旧兼容层；直接删除旧 spec 兼容读取、`FrAcddDtoKind.state/ignored`、以及相关旧示例与测试语义。
- 2026-06-11: 确认 `BFF` 的 `BFF-API:` 段落放在 `Models:` 之后，采用固定多行 block 模板；`<BASE>` 路径由 contract 文件路径稳定派生。
- 2026-06-11: 确认技能 spec 保留 `exportFormat` 字段名；其取值改为 `JSON` / `PROTO`，默认 `JSON`；`BFF-JSON` / `BFF-PROTO` 作为 `api` 的快捷写法。
- 2026-06-11: 确认 `JSON` 导出不要求 `@FrAcddField(tag: ...)`；空的 `@FrAcddField()` 注解应直接省略，仅在 `tag` / `wireName` / `nestedRef` / `include: false` 等非默认场景保留。
- 2026-07-17: 完成合同派生顺序修复：增加 contract/final 两阶段验证、Theme/BFF/stub 全量预检与失败回滚、PageArgs 字段转换校验，并禁止覆盖已实现的派生文件。
