# fr_acdd

Use this reference when a contract-first page will use `bffDto` mode and the
agent needs the `fr_acdd` annotation, DTO, and extraction rules.

`fr_acdd` provides:

- `@FrAcddPage`
- `@FrAcddDto`
- `@FrAcddField`
- `@FrAcddFreezed`
- the shared `fr_acdd:extract_bff_dto` CLI that renders either `proto` or
  `json5` output

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
@FrAcddFreezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    @FrAcddField(tag: 1)
    required String title,
  }) = _NotificationsScreenDataModel;
}
```

## Extraction CLI

After the contract file exists, export either `proto` or `json5` from that
contract:

```bash
fvm dart run fr_acdd:extract_bff_dto --format proto --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.proto
fvm dart run fr_acdd:extract_bff_dto --format json5 --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.json5
```

## Rules

- Prefer `@FrAcddFreezed` for extractable DTOs. `@Freezed(...)` is also
  supported.
- `@FrAcddDto` targets must stay single-constructor data classes; do not use
  Freezed unions for extractable DTOs.
- `@FrAcddDto` is only for backend-transfer DTOs. Do not annotate page-local
  state classes as DTO kinds.
- In `bffDto` mode, keep the `API:` comment section as a string list with one
  upstream API branch per line. `fr_acdd` will carry those paths and branch
  descriptions into both output formats, and will only infer branches when the
  `API:` section is missing.
- `FrAcddMode` only expresses `api` versus `bffDto`. `proto` and `json5` are
  derived output formats selected in the CLI, not extra contract modes.
- Included `root` and `nested` fields must declare explicit
  `@FrAcddField(tag: ...)` values for `proto` export.
- Keep `Figma:`, `API:`, and `Route:` doc comments above the root widget so
  `fr_acdd` can carry them into generated headers.
