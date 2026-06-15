# fr_acdd

Use this reference when a contract-first page will use `bff` mode and the
agent needs the `fr_acdd` annotation, DTO, and extraction rules.

`fr_acdd` provides:

- `@FrAcddPage`
- `@FrAcddDto`
- `@FrAcddField`
- `@FrAcddFreezed`
- the shared `fr_acdd:extract_bff` CLI that renders either `proto` or
  `json5` output

## Minimal contract markers

```dart
import 'package:fr_acdd/fr_acdd.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'notifications_page',
)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    required String title,
  }) = _NotificationsScreenDataModel;
}
```

## Extraction CLI

After the contract file exists, export either `proto` or `json5` from that
contract:

```bash
fvm dart run fr_acdd:extract_bff --format proto --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.proto
fvm dart run fr_acdd:extract_bff --format json5 --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.md
```

## Rules

- Prefer `@FrAcddFreezed` for extractable DTOs. `@Freezed(...)` is also
  supported.
- `@FrAcddFreezed` is only the minimal extraction preset. It intentionally
  keeps `fromJson/toJson` off so the contract layer does not imply a runtime
  JSON boundary that may not exist.
- `@FrAcddDto` targets must stay single-constructor data classes; do not use
  Freezed unions for extractable DTOs.
- `@FrAcddDto` is only for backend-transfer DTOs. Do not annotate page-local
  state classes as DTO kinds.
- If a DTO really does cross a runtime JSON boundary, keep `@FrAcddDto` and
  replace `@FrAcddFreezed` with an explicit `@Freezed(...)` that enables
  `fromJson/toJson` plus the normal `factory Xxx.fromJson(...)` boilerplate.
- In `bff` mode, hide `API:`, keep the `BFF-API:` comment section below
  `Models:`, and render one multiline branch block per upstream API, for
  example
  `GET <BASE>/notifications-page/bootstrap` followed by
  `[NotificationsBootstrapReq], [NotificationsScreenDataModel]`.
- `fr_acdd` carries those method/path and DTO refs into both output formats,
  and only infers branches when the `BFF-API:` section is missing.
- `FrAcddMode` only expresses `api` versus `bff`. `proto` and `json5` are
  derived output formats selected in the CLI, not extra contract modes.
- `<BASE>` is derived from the page folder chain under `lib/page` or
  `lib/src/page`. For example:
  `lib/page/home_page/home_page.dart` -> `<BASE>/home-page/...`
  `lib/page/home_page/sub_page/sub_page.dart` -> `<BASE>/home-page/sub-page/...`
- For `json5` export, fields do not need protobuf tags. If a field would only
  use `@FrAcddField()` with no arguments, omit the annotation entirely.
- Included `root` and `nested` fields must declare explicit
  `@FrAcddField(tag: ...)` values for `proto` export.
- `wireName` defaults to the Dart field name, so omit it unless the exported
  wire field must differ.
- `nestedRef` is usually inferred from the Dart field type. Only set it
  manually when type inference would be ambiguous.
- Use `@FrAcddField(...)` only when you need `tag`, `wireName`, `nestedRef`,
  or `include: false`.
- `json5` export still produces a Markdown document with per-API JSON5
  request/response snippets. Treat it as a derived review artifact, not a
  second source of truth.
- Keep `Figma:`, the active API section (`API:` or `BFF-API:`), and `Route:`
  doc comments above the root widget so `fr_acdd` can carry them into
  generated headers.
