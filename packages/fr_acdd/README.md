# fr_acdd

Pure Dart annotations and extraction utilities for FlowR contract-first pages.

`fr_acdd` reads `@FrAcddPage`, `@FrAcddDto`, and `@FrAcddField` annotations
from a contract page, extracts a shared BFF DTO analysis, and then renders the
final artifact as either:

- `proto`
- `json5`

Recommended DTO preset:

```dart
@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    @FrAcddField(tag: 1)
    required String title,
  }) = _NotificationsScreenDataModel;
}
```

Use `@FrAcddFreezed` or `@Freezed(...)` for extractable DTOs.

Route, Figma, and API split metadata are copied from the contract doc comments
when the page follows the `fr-mvvm-contract` convention:

```dart
/// Figma: https://www.figma.com/file/...
/// API:
/// - GET /bff/notifications/bootstrap owns page bootstrap metadata.
/// - GET /bff/notifications/tabs owns tab payload loading.
/// Route: AppRouter.notifications
@FrAcddPage(
  mode: FrAcddMode.bffDto,
  namespace: 'notifications_page',
)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}
```

CLI:

```bash
fvm dart run fr_acdd:extract_bff_dto --format proto --input path/to/xxx_page.dart --output path/to/xxx_page.proto
fvm dart run fr_acdd:extract_bff_dto --format json5 --input path/to/xxx_page.dart --output path/to/xxx_page.json5
```

`FrAcddMode` only expresses the contract mode:

- `api`
- `bffDto`

The `--format` flag only selects the derived output format. Do not encode
`proto` or `json5` as contract modes.

If the contract comment omits the `API:` section, `fr_acdd` will infer
suggested BFF API branches from the root DTO UX shape instead of assuming one
page equals one API.

For `proto` export, every included root or nested field must declare
`@FrAcddField(tag: ...)`. The extractor will fail fast when tags are missing,
duplicated, or use the reserved range `19000-19999`.

`@FrAcddDto` is only for backend-transfer DTOs. Keep page-local state in
unannotated page models or view-model members instead of trying to encode local
state as a DTO kind.
