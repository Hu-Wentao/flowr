# fr_acdd

Use this reference when a contract-first page will use `bffDto` mode and the
agent needs the `fr_acdd` annotation, DTO, and extraction rules.

`fr_acdd` provides:

- `@FrAcddPage`
- `@FrAcddDto`
- `@FrAcddField`
- the `fr_acdd:extract_bff_dto` CLI that renders `.proto` output

## Minimal contract markers

```dart
import 'package:fr_acdd/fr_acdd.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

@FrAcddPage(
  mode: FrAcddMode.bffDto,
  namespace: 'notifications_page',
)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}

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

## Extraction CLI

After the contract file exists, extract the BFF DTO schema as `.proto`:

```bash
fvm dart run fr_acdd:extract_bff_dto --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.proto
```

## Rules

- `@FrAcddDto` targets must use explicit `@Freezed(...)`, not `@freezed`.
- `@FrAcddDto` targets must stay single-constructor data classes; do not use
  Freezed unions for extractable DTOs.
- Included `root` and `nested` fields must declare explicit
  `@FrAcddField(tag: ...)` values for protobuf safety.
- Keep `Figma:` and `Route:` doc comments above the root widget so `fr_acdd`
  can carry them into the generated `.proto` header.
