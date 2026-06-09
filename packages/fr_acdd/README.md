# fr_acdd

Pure Dart annotations and extraction utilities for FlowR contract-first pages.

`fr_acdd` reads `@FrAcddPage`, `@FrAcddDto`, and `@FrAcddField` annotations
from a contract page, extracts a shared BFF DTO analysis, and then renders the
final artifact as either:

- `BFF-DTO-PROTO`: `.proto`
- `BFF-DTO-JSON`: `.json5`

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

`@Freezed(...)` and legacy `@freezed` are still accepted, but
`@FrAcddFreezed` keeps the DTO preset short and explicit.

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

If the contract comment omits the `API:` section, `fr_acdd` will infer
suggested BFF API branches from the root DTO UX shape instead of assuming one
page equals one API.

For `BFF-DTO-PROTO`, every included root or nested field must declare
`@FrAcddField(tag: ...)`. The extractor will fail fast when tags are missing,
duplicated, or use the reserved range `19000-19999`.
