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
  - `BFF-DTO`
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
  - `api = BFF-DTO`
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

## 任务列表

### A. 技能文档修订

- [ ] A1. 更新 `SKILL.md` 的输入门禁说明
  - 明确 `figmaUrl` 与 `api` 为必填输入
  - 明确 `api` 的三种合法取值与语义
  - 明确缺少输入时不能直接生成页面

- [ ] A2. 更新 `SKILL.md` 的前置分析流程
  - 先读 Figma
  - 再读邻近页面、组件、theme 约束
  - 最后按 `api` 取值进入不同分析分支

- [ ] A3. 更新 `SKILL.md` 的页面生成规则
  - 删除“单独数值定义类”相关生成约定
  - 增加“固定值与响应式约束的取舍原则”

### B. 上下文分析脚本修订

- [ ] B1. 更新 `page_context.py` 的输出提示词
  - 明确要求先检查 `figmaUrl`
  - 明确要求先检查 `api`
  - 明确 `NONE`、`BFF-DTO`、`<有效API地址>` 三种分支行为

- [ ] B2. 补充邻近页面/组件/theme 分析提示
  - 让上下文输出中显式包含这些约束

### C. 生成器修订

- [ ] C1. 更新 `new_page.py` 的输入约束
  - 明确 spec 中对应字段是否必填
  - 明确 `api` 三种形态的处理策略

- [ ] C2. 更新生成代码的布局策略
  - 不再输出 `_XxxPageDimens` 之类的常量类
  - 直接在 UI 中使用数值
  - 保留对自适应布局的优先指导，不把 Figma 固定值直接绝对化

- [ ] C3. 检查示例与模板
  - 避免示例代码继续引导出单独数值类
  - 如有必要，补一个 `NONE` / `BFF-DTO` / 有效 API 地址的示例

### D. 文档联动修订

- [ ] D1. 检查 `skills/README.md` 是否需要同步更新
- [ ] D2. 检查 `fr-acdd` 参考文档是否需要同步补充 `BFF-DTO` 输入门禁

### E. 验证与回归

- [ ] E1. 文档验证
  - 确认 `SKILL.md`、README、参考文档之间的描述一致

- [ ] E2. 生成器冒烟验证
  - 用 `api = NONE` 生成一次
  - 用 `api = BFF-DTO` 生成一次
  - 用 `api = <有效API地址>` 的示例 spec 验证一次

- [ ] E3. 输出结构验证
  - 确认不再生成单独的尺寸常量类
  - 确认页面仍保持 contract / view / viewModel 分层
  - 确认生成结果没有引入隐藏兼容开关

## 待确认细节

- [ ] `figmaUrl` 和 `api` 在最终 spec 中的字段名是否固定为这两个名字
- [ ] 若用户未提供 `figmaUrl` 或 `api`，是直接报错终止，还是输出待补全提示
- [ ] `api = <有效API地址>` 的“有效”判定标准
  - 仅 URL 格式合法
  - 还是必须可读取并可解析
- [ ] `api = NONE` 时，contract 注释中的 `API` 段落如何写
- [ ] `api = BFF-DTO` 时，contract 注释中的 `API` 段落是否需要固定模板
- [ ] “直接在 UI 中使用数值”是否允许局部 `const double` 变量
- [ ] 响应式布局的推荐手段是否要在技能中明确排序

## 执行顺序建议

1. 先修订 `SKILL.md`，锁定规则。
2. 再修订 `page_context.py`，让分析提示与规则一致。
3. 再修订 `new_page.py`，落地到生成行为。
4. 最后做 README / reference 联动和冒烟验证。

## 变更记录

- 2026-06-11: 初始化任务清单，录入首批修订目标，尚未开始实现。
