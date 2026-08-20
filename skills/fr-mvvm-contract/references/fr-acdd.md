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
import 'package:flutter/material.dart';
import 'package:flutter/widget_previews.dart';

Widget notificationsPreviewWrapper(Widget child) => MaterialApp(home: child);

@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'notifications_page',
)
class NotificationsView extends StatelessWidget {
  @Preview(
    name: 'Notifications',
    group: 'notifications_page',
    size: Size(360, 780),
    wrapper: notificationsPreviewWrapper,
  )
  const NotificationsView({super.key});
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

## Version preflight

BFF v9 and library-shell multi-endpoint extraction require `fr_acdd >= 0.7.0`.
Check the resolved Pub package, and attempt a compatible upgrade, before
contract generation or refresh:

```bash
uv run --script <skill-root>/scripts/ensure_fr_acdd.py --project-root <owning-package>
```

The command uses `pub add fr_acdd:^0.7.0` for missing or old hosted
dependencies. It retains path/git source ownership and tries
`pub upgrade fr_acdd`; when that source still reports an older version, update
its revision or checkout manually. Use `ensure_fr_acdd.py --check` for a
read-only dependency CI gate. Normal `generate_bff.py` execution performs this
upgrade attempt automatically; `generate_bff.py --check` does not edit Pub
dependency declarations or lockfiles, but it still executes Dart/extractor
checks and may touch tool caches or temporary files. Run `ensure_fr_acdd.py`
explicitly before `generate_from_contract.py` so dependency mutation remains
outside that generator's transactional artifact plan.

## Extraction CLI

After the contract file exists, export either `proto` or `json5` from that
contract:

```bash
fvm dart run fr_acdd:extract_bff --format proto --input lib/page/notifications_page/notifications_page.dart --output /tmp/notifications_page.proto
fvm dart run fr_acdd:extract_bff --format json5 --input lib/app/notifications/notifications.dart --output lib/app/notifications/notifications.bff.md
```

## Rules

- Read `widget-preview.md` and put Flutter SDK `@Preview(...)` on the public
  constructor of every newly generated Widget carrying `@FrAcddPage`.
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
- Every `XxxBffReq` referenced by `BFF-API:` must additionally declare
  `Map<String, dynamic> toJson();` in the abstract contract class. This makes
  the serializer visible to Retrofit when the typed request is used directly
  as `@Body()` or `@Queries()`.
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
- Pass the component library shell `xxx.dart` to the extractor. It aggregates
  the shell and authored `part` files, so `@FrAcddPage` may live in `.v.dart`
  while `BFF-API:` and DTOs live in `.c.dart`. It skips missing/generated
  `.freezed.dart` and `.g.dart` parts and rejects a part file as `--input`.
- Treat JSON5 extraction as the UI-facing BFF API input to required component
  delivery in BFF-JSON mode. `generate_bff.py` wraps it in compact
  `bff-md-meta/v9` identity/source YAML Front Matter and renders the UI/backend
  authority Markdown defined by `bff-dual-authority.md`. Generate to a temporary file and replace
  `xxx.bff.md` only after extraction and wrapping succeed; use
  `generate_bff.py --check` to detect missing or stale output.
- Check the resolved `fr_acdd` version before extractor compilation; a loose
  declaration such as `any` is not evidence that Pub resolved `>= 0.7.0`.
- Preflight `fvm dart run fr_acdd:extract_bff --help`. If compilation fails,
  report the resolved `fr_acdd`/analyzer incompatibility and stop. Do not skip
  extraction.
- Read `api-contract-semantics.md` and `frontend-interactions.md` before
  defining BFF DTO fields. In `bff` mode, hide `API:`, keep the UI-facing
  canonical `BFF-API:` comment section below
  `Models:`, and render one multiline branch block per upstream API, for
  example
  `GET <BASE>/notifications` followed by
  `[NotificationsDataBffReq], [NotificationsDataBffRsp]`.
- `fr_acdd` carries those method/path and DTO refs into both output formats,
  emitting `## BFF-API` for JSON5. It does not extract Behaviors or
  Interactions; the Python contract layer validates and projects them. It only
  infers API branches when the `BFF-API:` section is missing.
- `FrAcddMode` only expresses `api` versus `bff`. `proto` and `json5` are
  derived output formats selected in the CLI, not extra contract modes.
- Treat `namespace` and `version` on `@FrAcddPage` as the BFF contract identity
  and version. An omitted version is `1`; do not derive it from the
  `bff-md-meta` schema revision.
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
- `json5` extraction supplies per-UI-API JSON5 request/response snippets. The
  final Markdown keeps those inline UI API DTOs separate from backend OpenAPI
  operation references and call flow. Backend request/response schemas remain
  exclusively in `.openapi.json`. Treat the BFF Markdown as a derived review
  artifact, not a second backend schema source.
- Keep `Figma:`, the active API section (`API:` or `BFF-API:`), and `Route:`
  as unique consecutive documentation sections anywhere in the library shell
  or its authored parts. `fr_acdd` aggregates them into generated headers and
  rejects duplicate authority sections.
