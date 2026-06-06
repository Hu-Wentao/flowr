# fr_acdd

Pure Dart annotations and extraction utilities for FlowR contract-first pages.

`fr_acdd` reads `@FrAcddPage`, `@FrAcddDto`, and `@FrAcddField` annotations
from a contract page, extracts the root and nested DTO definitions, and renders
them as a `.proto` schema.

DTO classes must use explicit `@Freezed(...)` configuration. `@freezed` is
rejected so the generation contract stays visible and stable.

Recommended DTO annotation:

```dart
@FrAcddDto(kind: FrAcddDtoKind.root)
@Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
)
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    @FrAcddField(tag: 1)
    required String title,
  }) = _NotificationsScreenDataModel;
}
```

Route and Figma metadata are copied from the contract doc comments when the
page follows the `fr-mvvm-contract` convention:

```dart
/// Figma: https://www.figma.com/file/...
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
fvm dart run fr_acdd:extract_bff_dto --input path/to/xxx_page.dart --output path/to/xxx_page.proto
```

For protobuf safety, every included root or nested field must declare
`@FrAcddField(tag: ...)`. The extractor will fail fast when tags are missing,
duplicated, or use the reserved range `19000-19999`.
