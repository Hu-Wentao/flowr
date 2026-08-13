## 0.6.0 2026-08-13
* feat: split BFF UI API contracts from business API contracts
* feat: standardize generated contract type suffixes
* fix: constrain analyzer compatibility to verified versions
* docs: export and clarify `FrState` presets for MVVM state
* breaking: require BFF API request/response DTOs to use `XxxBffReq` / `XxxBffRsp` and internal transfer types to use `XxxDto`
* breaking: rename the generated BFF contract section from `BFF-API` to `BFF-UI-API`

## 0.5.1 2026-06-15
* docs: clarify page-local `FrState` guidance for contract-generated state models

## 0.5.0 2026-06-15
* feat: add `FrAcddFreezedJSON` preset for extractable JSON DTOs
* docs: clarify fr_acdd dto json boundary

## 0.4.0 2026-06-11
* feat: refine BFF contract export semantics and explicit `BFF-API` parsing
* feat: add the `extract_bff` CLI and an end-to-end example app
* fix: derive nested BFF page paths and restore wide analyzer compatibility for workspace publishing
* breaking: rename `FrAcddMode.bffDto` to `FrAcddMode.bff`
* breaking: remove `FrAcddDtoKind.state` and `FrAcddDtoKind.ignored`
* breaking: drop legacy `@freezed` / `@frAcddFreezed` acceptance and rename the old `extract_bff_dto` entrypoint to `extract_bff`

## 0.3.1 2026-06-09
* fix: relax analyzer compatibility so `fr_acdd` can resolve with `hive_generator ^2.0.1`

## 0.3.0 2026-06-09
* feat: add BFF JSON export with JSON5 output
* feat: carry API split analysis in shared BFF schema
* feat: infer suggested multi-API branches when API comments are missing

## 0.2.0 2026-06-06
* feat: add FrAcddFreezed preset
* feat: tighten freezed dto contract
* feat: add fr_acdd protobuf extractor
