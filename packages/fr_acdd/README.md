# fr_acdd

Pure Dart annotations and extraction utilities for FlowR contract-first pages.

`fr_acdd` reads `@FrAcddPage`, `@FrAcddDto`, and `@FrAcddField` annotations
from a contract page, extracts a shared BFF analysis, and then renders the
final artifact as either:

- `proto`
- `json5` request/response snippets rendered inside a Markdown document
  (recommended output suffix: `.md`)

Recommended DTO preset:

```dart
@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    required String title,
  }) = _NotificationsScreenDataModel;
}
```

Use `@FrAcddFreezed` or `@Freezed(...)` for extractable DTOs. Keep page-local
state on plain `@Freezed(...)` models without `@FrAcddDto`.

Route, Figma, and API split metadata are copied from the contract doc comments
when the page follows the `fr-mvvm-contract` convention:

```dart
/// Figma: https://www.figma.com/file/...
/// Route: AppRouter.notifications
/// Models:
/// - [NotificationsBootstrapReq]: bootstrap request dto
/// - [NotificationsScreenDataModel]: notification screen payload
/// BFF-API:
/// - GET <BASE>/notifications-page/bootstrap
///   [NotificationsBootstrapReq], [NotificationsScreenDataModel]
/// - GET <BASE>/notifications-page/tabs
///   [NotificationsTabsReq], [NotificationsTabDataModel]
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'notifications_page',
)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}
```

CLI:

```bash
fvm dart run fr_acdd:extract_bff --format proto --input path/to/xxx_page.dart --output path/to/xxx_page.proto
fvm dart run fr_acdd:extract_bff --format json5 --input path/to/xxx_page.dart --output path/to/xxx_page.md
```

`FrAcddMode` only expresses the contract mode:

- `api`
- `bff`

The `--format` flag only selects the derived output format. Do not encode
`proto` or `json5` as contract modes.

If the contract comment omits the `BFF-API:` section, `fr_acdd` will infer
suggested BFF API branches from the root DTO UX shape instead of assuming one
page equals one API.

For `proto` export, every included root or nested field must declare
`@FrAcddField(tag: ...)`. The extractor will fail fast when tags are missing,
duplicated, or use the reserved range `19000-19999`.

For `json5` export, tags are not required. If a field annotation would be just
`@FrAcddField()`, omit it entirely.

`wireName` defaults to the Dart field name. Omit it unless the exported wire
field must differ from the contract field name.

`nestedRef` is usually inferred from Dart field types, including DTO objects,
lists, sets, and maps. Only set it explicitly when inference would be
ambiguous.

Use `@FrAcddField(...)` only when the field needs `tag`, `wireName`,
`nestedRef`, or `include: false`.

`@FrAcddDto` is only for backend-transfer DTOs. Keep page-local state in
unannotated page models or view-model members instead of trying to encode local
state as a DTO kind.
