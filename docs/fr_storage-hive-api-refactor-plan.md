# `fr_storage` Hive 风格 API 重构方案

> 状态：方案已确认，待实施。
>
> 目标：将 `fr_storage` 的公开 API 收敛为唯一的 `Storage -> Box -> CRUD`
> 风格，同时保留默认单库的简单调用和多目录、多密钥实例能力。

## 1. 背景与最终决定

当前 `fr_storage` 使用实例加 scope 参数的接口：

```dart
await FrStorage.instance.init();
await FrStorage.instance.saveValue('settings', 'theme', 'dark');
final theme = FrStorage.instance.value('settings', 'theme');
```

这套接口能够完成加密字符串 CRUD，但存在以下使用成本：

- 默认场景反复出现 `FrStorage.instance`。
- 每次操作都要重复传入 scope，业务代码容易误用命名空间。
- `value/saveValue/removeValue/clearScope` 与 Hive 用户熟悉的
  `get/put/delete/clear` 心智模型不同。
- 默认 singleton 和公开构造函数形成两种入口，文档与依赖注入方式不够统一。

本次重构确认采用以下决定：

1. 数据访问只保留 Hive 风格的 Box API。
2. 默认数据库只通过静态 `FrStorage.init/box/close` 管理。
3. 多数据库只通过 `FrStorage.newInstance()` 创建。
4. 默认库与多实例都通过相同的 `FrBox` 执行 CRUD。
5. 删除旧的 scope 参数 API、`FrStorage.instance`、公开构造函数和
   `KeyValueStorage`。
6. 不复制 Hive 的泛型对象、adapter、监听、lazy box 等完整功能；首版仍是
   加密字符串键值存储。

本文档取代 `fr_storage-implementation-plan.md` 中关于公开 API 和生命周期的
设计；原文的数据模型、加密格式与安全约束继续有效。

## 2. 目标与非目标

### 2.1 本次目标

- 默认场景使用 `FrStorage.init()`，不再暴露 `.instance`。
- 使用 box name 代替原来的 scope 参数。
- 提供同步 `get/containsKey` 和异步 `put/delete/clear`。
- 同名 box 在同一 storage owner 内返回相同缓存实例。
- 通过 `FrStorage.newInstance()` 恢复独立目录、独立 secure-storage key 和独立
  AES key 的多实例能力。
- 默认库与独立实例具有互不影响的生命周期和 box 缓存。
- 保留当前 ObjectBox schema、HMAC 索引、AES-256-GCM payload 和错误密钥检测。
- 更新 README、example、测试和 `flowr-usage` skill reference，使其只展示一种
  CRUD 风格。

### 2.2 非目标

- 不支持 Web。
- 不增加非字符串值、泛型 `FrBox<T>` 或对象序列化。
- 不增加 type adapter、自动递增 key、批量写入、事务、TTL、监听流、
  `ValueListenable` 或 lazy box。
- 不增加 box 级 `close()`；一个 owner 下的 box 共享同一个 ObjectBox Store。
- 不读取或迁移模板项目 `AppStorage` 的数据库。
- 不改变现有持久化 entity、模型 UID 或 payload 编码格式。

## 3. 最终公开 API

包入口保持：

```dart
import 'package:fr_storage/fr_storage.dart';
```

公开入口只导出 `FrStorage`、`FrStorageInstance` 和 `FrBox`：

```dart
abstract final class FrStorage {
  static const defaultSecureStorageKey = 'fr_storage_key_v1';

  static bool get isInitialized;

  static Future<void> init({
    String? directory,
    String secureStorageKey = defaultSecureStorageKey,
    FlutterSecureStorage? secureStorage,
    Uint8List? encryptionKey,
  });

  static FrBox box(String name);

  static Future<FrStorageInstance> newInstance({
    required String directory,
    required String secureStorageKey,
    FlutterSecureStorage? secureStorage,
    Uint8List? encryptionKey,
  });

  static Future<void> close();
}

abstract interface class FrStorageInstance {
  bool get isInitialized;

  FrBox box(String name);

  Future<void> close();
}

abstract interface class FrBox {
  String get name;

  bool containsKey(String key);

  String? get(
    String key, {
    String? defaultValue,
  });

  Future<void> put(String key, String value);

  Future<void> delete(String key);

  Future<void> clear();
}
```

设计约束：

- `FrStorage` 是不可实例化的默认库门面。
- `FrStorageInstance` 只由 `FrStorage.newInstance()` 返回，不提供公共构造函数或
  二次 `init()`。
- `newInstance()` 在返回前完成 ObjectBox、密钥和内部 marker 初始化。
- `FrBox` 是业务代码和 Repository 优先依赖的最小接口。
- 不提供 `FrStorage.value/saveValue` 之类的静态快捷方法，避免形成第二套 CRUD
  风格。
- 不公开 ObjectBox `Store`、entity、查询属性或生成模型。

## 4. 使用方式

### 4.1 默认单库

```dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.init();

  final settings = FrStorage.box('settings');
  await settings.put('theme', 'dark');

  final theme = settings.get(
    'theme',
    defaultValue: 'system',
  );

  runApp(MyApp(theme: theme));
}
```

应用关闭或测试 teardown：

```dart
await FrStorage.close();
```

### 4.2 多实例

`newInstance()` 的 `directory` 和 `secureStorageKey` 必填，防止独立实例意外复用
默认库的数据目录或密钥条目：

```dart
final accountStorage = await FrStorage.newInstance(
  directory: accountDirectory,
  secureStorageKey: 'account_42_storage_key_v1',
);

final session = accountStorage.box('session');
await session.put('token', token);

final savedToken = session.get('token');

await accountStorage.close();
```

### 4.3 依赖注入

业务对象优先依赖具体命名空间对应的 `FrBox`：

```dart
final class SessionRepository {
  SessionRepository(this._box);

  final FrBox _box;

  String? get token => _box.get('token');

  Future<void> saveToken(String token) => _box.put('token', token);

  Future<void> clear() => _box.clear();
}
```

组装代码：

```dart
final sessionRepository = SessionRepository(
  FrStorage.box('session'),
);
```

需要动态选择多个 box 或统一关闭独立数据库时，可以注入
`FrStorageInstance`；不再提供 storage-wide CRUD interface。

### 4.4 测试

测试仍可用固定 32-byte key 绕过平台 secure storage：

```dart
final directory = await Directory.systemTemp.createTemp('fr_storage_test_');
final storage = await FrStorage.newInstance(
  directory: directory.path,
  secureStorageKey: 'unused_in_test',
  encryptionKey: Uint8List(32),
);

final box = storage.box('test');

addTearDown(() async {
  await storage.close();
  await directory.delete(recursive: true);
});
```

## 5. 生命周期与错误语义

| 场景 | 预期行为 |
| --- | --- |
| 默认库未 init 时读取 `FrStorage.isInitialized` | 返回 `false` |
| 默认库未 init 时调用 `FrStorage.box(name)` | 抛 `StateError` |
| 已 init 后再次 `FrStorage.init()` | 串行关闭旧 owner、使旧 box 失效，再打开新配置 |
| `FrStorage.close()` 多次调用 | 幂等，返回已完成的 `Future<void>` |
| `newInstance()` 成功 | 返回已经初始化且可立即 `box()` 的实例 |
| `newInstance()` 失败 | 清理部分 Store/key 状态，不返回实例 |
| `FrStorageInstance.close()` 多次调用 | 幂等 |
| owner 关闭后使用旧 `FrBox` | 抛 `StateError` |
| 同 owner、同 name 重复 `box()` | 返回 identical 的缓存实例 |
| 不同 owner 使用同 name | 返回相互独立的 box |
| key 不存在时 `get()` | 返回 `defaultValue`，默认 `null` |
| 保存了空字符串时 `get()` | 返回空字符串，不与 key 不存在混淆 |
| 未初始化或已关闭时执行 box CRUD | 抛 `StateError` |
| 注入 key 不是 32 bytes | init/newInstance 抛 `ArgumentError` |
| secure storage key 非法 | init/newInstance 抛 `StateError`，不覆盖原值 |
| 错误 AES key | init/newInstance 校验 marker 时抛 `StateError` |
| payload 版本未知、认证失败或绑定不匹配 | `get()` 抛 `StateError`，不删除数据 |
| 两个存活 owner 打开同一目录 | 明确失败，不共享同一个 ObjectBox Store |

生命周期实现要求：

- 默认 owner 的 `init/close` 必须串行化。
- 独立实例创建过程必须原子化：失败时不注册目录、不缓存 box。
- `close()` 改为异步 API，以便生命周期队列完成后再向调用方返回。
- CRUD 默认限定为单 isolate 串行使用；不承诺高层跨 isolate 语义。
- 每个 owner 都维护自己的 generation 或 closed token，确保旧 `FrBox` 不会在
  re-init 后意外操作新 Store。

## 6. Box 语义

box name 是原 scope 的唯一替代：

```text
FrStorage.box("settings")
├── get("theme")
├── put("theme", "dark")
├── delete("theme")
└── clear()
```

规则：

- box name 和 key 均保持字符串、大小写敏感。
- `containsKey` 与 `get` 为同步查询。
- `put/delete/clear` 返回 `Future<void>`；调用方应 await 持久化操作。
- `clear()` 只删除当前 box 的业务记录，不影响同 owner 下其他 box，也不能删除
  内部密钥验证 marker。
- `FrBox` 不提供 `close()`，因为多个 box 共享 owner 的 Store 和 encryption key。
- `FrBox` 不承诺 `keys/values/length`；当前 keyed HMAC 索引和加密 payload 的设计
  不应为了模仿 Hive 而扩大首版数据遍历能力。

## 7. 数据与加密兼容性

本次只重构公开 API 和 owner/box 包装，不修改持久化格式：

- `FrStorageEntry` 仍包含 `id`、`scopeHash`、`keyHash`、`payload`。
- box name 作为原 scope 参与 HMAC：

  ```text
  scopeHash = HMAC-SHA256(encryptionKey, "scope\0" + boxName)
  keyHash   = HMAC-SHA256(encryptionKey, "key\0" + boxName + "\0" + key)
  ```

- payload 仍为 AES-256-GCM：

  ```text
  v1:<base64url nonce>:<base64url cipherTextAndTag>
  ```

- 解密 JSON 仍核对保存的 scope/key；实现内部将 scope 变量语义改称 box name，但
  payload 字段名不变，以保持数据兼容。
- 内部加密 marker、ObjectBox model UID 和生成代码保持不变。
- 使用相同 directory 与 AES key 时，新 API 必须能读取重构前 `fr_storage` 创建的
  数据。
- 仍然不兼容模板项目 `AppStorage` 的数据库。

因此本次不应重新生成或修改 `objectbox-model.json` 和 `objectbox.g.dart`。若生成
文件发生 diff，应停止并检查是否意外修改了 entity/schema。

## 8. 内部实现建议

推荐将共享生命周期抽为不导出的 owner：

```text
FrStorage (static default facade)
└── _FrStorageOwner defaultOwner
    ├── Store / Box<FrStorageEntry>
    ├── encryptionKey
    ├── lifecycle queue
    ├── generation
    └── Map<String, _FrBox> boxes

_FrStorageInstance implements FrStorageInstance
└── _FrStorageOwner owner
    └── Map<String, _FrBox> boxes

_FrBox implements FrBox
└── owner + ownerGeneration + boxName
```

实现原则：

- `_FrStorageOwner` 复用当前密钥读取、HMAC、AES-GCM、查询和 marker 逻辑。
- `_FrBox` 只绑定 name，并把 CRUD 委托给 owner；不持有 ObjectBox public type。
- owner 每次成功打开时生成新的 generation。
- `_FrBox` 每次操作前核对 owner 未关闭且 generation 未变化。
- owner close 时清空 box cache、密钥和 Store，并使所有既有 box 失效。
- 默认 owner 与独立 owner 使用完全相同的内部实现，避免安全逻辑分叉。
- 可选的 `FlutterSecureStorage` 仅用于密钥读写注入，不暴露在 `FrBox`。

## 9. Breaking changes 与迁移映射

本次是明确的公开 API breaking change：

- 删除 `FrStorage.instance`。
- 删除 `FrStorage(...)` 公共构造函数。
- 删除 `KeyValueStorage`。
- 删除 `hasValue(scope, key)`。
- 删除 `value(scope, key)`。
- 删除 `saveValue(scope, key, value)`。
- 删除 `removeValue(scope, key)`。
- 删除 `clearScope(scope)`。
- `close()` 从同步 `void` 改为 `Future<void>`。
- 未 init 的宽容读取改为 `FrStorage.box()` 立即抛错。

迁移映射：

| 重构前 | 重构后 |
| --- | --- |
| `await FrStorage.instance.init()` | `await FrStorage.init()` |
| `FrStorage.instance.hasValue(s, k)` | `FrStorage.box(s).containsKey(k)` |
| `FrStorage.instance.value(s, k)` | `FrStorage.box(s).get(k)` |
| `value(s, k, defaultValue: v)` | `box(s).get(k, defaultValue: v)` |
| `saveValue(s, k, v)` | `box(s).put(k, v)` |
| `removeValue(s, k)` | `box(s).delete(k)` |
| `clearScope(s)` | `box(s).clear()` |
| `FrStorage(...); await init(...)` | `await FrStorage.newInstance(...)` |
| `storage.close()` | `await storage.close()` |
| 注入 `KeyValueStorage` | 注入目标 `FrBox` 或 `FrStorageInstance` |

版本策略：

- 若 `0.1.0` 尚未发布，可以在首次发布前直接替换 API，并在 CHANGELOG 标明最终
  首版接口。
- 若 `0.1.0` 已发布，应升级到 `0.2.0`，在 CHANGELOG 完整列出以上 breaking
  changes。
- 不提供 deprecated 兼容层，因为目标是只保留一种数据访问风格。

## 10. 文件变更范围

预计修改：

```text
packages/fr_storage/
├── CHANGELOG.md
├── README.md
├── example/lib/main.dart
├── lib/
│   ├── fr_storage.dart
│   └── src/
│       ├── fr_box.dart                 # 新增公开接口
│       ├── fr_storage.dart             # 改为静态 facade
│       ├── fr_storage_instance.dart    # 新增公开接口与内部实现
│       ├── fr_storage_owner.dart       # 可选：共享内部生命周期
│       ├── fr_storage_entry.dart       # 不改 schema
│       └── key_value_storage.dart      # 删除
└── test/
    ├── fr_storage_test.dart
    ├── fr_storage_instance_test.dart   # 可新增
    ├── fr_storage_encryption_test.dart
    └── test_utils.dart

skills/flowr-usage/
├── SKILL.md                            # reference 描述按最终 API 调整
└── references/fr-storage.md            # 只保留 Box 风格示例
```

不得修改：

- `packages/fr_storage/lib/objectbox-model.json`
- `packages/fr_storage/lib/objectbox.g.dart`
- `template-app` 或外部参考项目

## 11. 分阶段实施步骤

### 阶段 A：建立 owner 与 Box API

1. 抽取 `_FrStorageOwner`，迁移当前 Store、key、marker、HMAC 和 AES-GCM 逻辑。
2. 新增 `FrBox` 接口和 `_FrBox` 实现。
3. 实现 box cache、owner generation 和关闭后失效检查。
4. 保持 entity 和 ObjectBox 生成文件不变。

### 阶段 B：默认静态 facade

1. 将 `FrStorage` 改为不可实例化的静态 facade。
2. 实现默认 owner 的 `init/isInitialized/box/close`。
3. 串行化默认 owner 的 init/close。
4. 删除 `.instance` 和旧 scope CRUD。

### 阶段 C：多实例

1. 新增 `FrStorageInstance` 接口与内部实现。
2. 实现 `FrStorage.newInstance()` 的原子创建和初始化。
3. 强制独立实例传入 directory 与 secureStorageKey。
4. 验证默认 owner 与多个独立 owner 可同时工作且互不影响。

### 阶段 D：迁移文档与测试

1. 将现有测试迁移到 Box API，不保留旧 API 示例。
2. 增加默认库、多实例、box identity、失效句柄和目录冲突测试。
3. 更新 README、example、CHANGELOG 和 skill reference。
4. 确认 barrel 只导出 `FrStorage`、`FrStorageInstance` 和 `FrBox`。

### 阶段 E：验证与发布准备

1. 确认 ObjectBox model/generated code 无 diff。
2. 运行格式化、分析、测试和 package dry-run。
3. 根据 `0.1.0` 是否已发布决定保留版本或升级到 `0.2.0`。
4. 列出 breaking changes 和平台兼容配置后提交。

## 12. 测试矩阵

至少覆盖：

1. 默认库未 init 时 `isInitialized == false`，`box()` 抛 `StateError`。
2. 默认库 init 后可取得 box，完成 contains/get/put/delete/clear。
3. key 不存在时 `get()` 返回 null 或指定 default；空字符串保持可区分。
4. 同 owner 同名 box 返回 identical；不同 box 数据隔离。
5. 默认库 close 幂等，close 后旧 box 所有操作抛 `StateError`。
6. 默认库 re-init 后旧 box 失效，新 box 可用。
7. `newInstance()` 返回已初始化实例，不需要再次 init。
8. 两个独立目录、独立 key 的实例可同时读写同名 box 且互不影响。
9. 关闭一个独立实例不影响默认库或其他实例。
10. 同一目录被两个存活 owner 打开时显式失败。
11. 16/24/31/33-byte key 被拒绝，只接受 32 bytes。
12. 固定 key 下 close 后重新 newInstance 可读取原数据。
13. 错误 key 打开已有目录时在初始化阶段抛 `StateError`。
14. payload nonce、明文泄露、版本篡改、认证篡改和 scope/key 绑定测试继续通过。
15. 重构前创建的数据在相同 directory/key 下可由 Box API 读取。
16. init/newInstance 失败后没有残留 Store、owner、box cache 或目录注册状态。
17. 公共 barrel 不导出 entity、ObjectBox 类型或旧 `KeyValueStorage`。

所有文件型测试使用临时目录；tearDown 必须先 await owner close，再递归删除目录。
ObjectBox desktop test runtime 继续使用本机/CI 安装的原生库，不把动态库提交进 package。

## 13. 验证命令

所有 Flutter/Dart 命令使用 FVM：

```bash
fvm flutter pub get
fvm dart format packages/fr_storage
fvm flutter analyze packages/fr_storage
fvm flutter test packages/fr_storage
cd packages/fr_storage && fvm dart pub publish --dry-run
```

skill 更新后额外运行：

```bash
uv run --with pyyaml python \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/flowr-usage
```

生成前后运行：

```bash
git diff --check
git diff -- packages/fr_storage/lib/objectbox-model.json \
  packages/fr_storage/lib/objectbox.g.dart
```

## 14. 完成标准

- 新用户只需要理解 `FrStorage -> FrBox -> get/put/delete/clear`。
- 默认库调用中不再出现 `.instance`。
- 多实例只通过 `FrStorage.newInstance()` 创建，并在返回时已完成初始化。
- 默认库和独立实例共享同一内部安全实现，但生命周期与 box cache 相互隔离。
- 公开入口不包含旧 scope CRUD、公共构造函数或 `KeyValueStorage`。
- 所有现有加密、持久化、错误密钥和明文泄露保证继续成立。
- 相同 directory/key 下的数据格式保持兼容，ObjectBox schema 与 UID 无变化。
- README、example、CHANGELOG、测试和 skill reference 只展示 Box 风格。
- analyze、test、publish dry-run 和 skill validation 全部通过。
- 最终交付明确列出 breaking changes；不提供隐藏兼容开关或双 API 风格。
