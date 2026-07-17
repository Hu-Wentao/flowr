# fr_acdd

Use this reference when a contract-first page will use `bff` mode and the
agent needs the `fr_acdd` annotation, DTO, and extraction rules.

`fr_acdd` provides:

- `@FrAcddPage`
- `@FrAcddDto`
- `@FrAcddField`
- `@FrAcddFreezed`
- `@FrAcddFreezedJSON`
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
@FrAcddFreezedJSON
class NotificationsDataBffRsp with _$NotificationsDataBffRsp {
  const factory NotificationsDataBffRsp({
    required String title,
  }) = _NotificationsDataBffRsp;

  factory NotificationsDataBffRsp.fromJson(Map<String, dynamic> json) =>
      _$NotificationsDataBffRspFromJson(json);
}
```

## Extraction CLI

After the contract file exists, export either `proto` or `json5` from that
contract:

```bash
fvm dart run fr_acdd:extract_bff --format proto --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.proto
fvm dart run fr_acdd:extract_bff --format json5 --input lib/app/notifications/notifications.c.dart --output lib/app/notifications/notifications.bff.md
```

## Rules

- Prefer `@FrAcddFreezed` for `PROTO`-style extractable DTOs and
  `@FrAcddFreezedJSON` for `JSON`-style extractable DTOs. `@Freezed(...)` is
  also supported.
- `@FrAcddFreezed` is only the minimal extraction preset. It intentionally
  keeps `fromJson/toJson` off so the contract layer does not imply a runtime
  JSON boundary that may not exist.
- `@FrAcddFreezedJSON` enables `fromJson/toJson` for extractable DTOs that
  also cross a runtime JSON boundary. It still requires the normal
  `factory Xxx.fromJson(...)` boilerplate and a generated `.g.dart` part in
  the owning contract library.
- `@FrAcddDto` targets must stay single-constructor data classes; do not use
  Freezed unions for extractable DTOs.
- Name every DTO referenced as an API request `XxxBffReq`, every DTO referenced
  as an API response `XxxBffRsp`, and DTOs used only inside those boundaries
  `XxxDto`.
- `@FrAcddDto` is only for backend-transfer DTOs. Do not annotate page-local
  state classes as DTO kinds. In `fr-mvvm-contract`, page-local models now
  default to FlowR's exported `@FrState` preset so `toJson()` is available for
  debugging. Use `@FrStateJson` only when the state model truly needs
  `fromJson()`, and fall back to plain `@Freezed(...)` when the model contains
  runtime-only or non-JSON-serializable fields.
- If a DTO really does cross a runtime JSON boundary, keep `@FrAcddDto` and
  prefer `@FrAcddFreezedJSON`. Use explicit `@Freezed(...)` only when that
  DTO needs custom Freezed options beyond the JSON preset.
- In `BFF-JSON` mode, generated DTO contracts should use `@FrAcddFreezedJSON`
  instead of `@FrAcddFreezed`.
- Pass `xxx.c.dart` to the extractor. It parses one compilation unit and does
  not follow the component shell's `part` directives.
- Treat JSON5 output as required component delivery in BFF-JSON mode. Generate
  to a temporary file and replace `xxx.bff.md` only after extraction succeeds;
  use `generate_bff.py --check` to detect missing or stale output.
- Preflight `fvm dart run fr_acdd:extract_bff --help`. If compilation fails,
  report the resolved `fr_acdd`/analyzer incompatibility and stop. Do not skip
  extraction.
- Read `api-contract-semantics.md` before defining BFF DTO fields. In `bff`
  mode, hide `API:`, keep the `BFF-API:` comment section below
  `Models:`, and render one multiline branch block per upstream API, for
  example
  `GET <BASE>/notifications` followed by
  `[NotificationsDataBffReq], [NotificationsDataBffRsp]`.
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
