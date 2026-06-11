# example_fr_acdd

`fr_acdd` contract-first home page example.

Source design:

- Figma: [Colorful Stock App iOS UI Kit Community](https://www.figma.com/design/8o2jFlD9xlVHQYmp2ddidb/Colorful-Stock-App---iOS-UI-Kit--Community-?node-id=14-11&t=BobLQ33X6rW4neR8-4)
- API mode: `BFF-DTO`

Key files:

- `lib/page/home_page/home_page.dart`
  The long-lived contract source of truth.
- `lib/page/home_page/home_page.v.dart`
  View widgets.
- `lib/page/home_page/home_page.vm.dart`
  Events and `FrBlocViewModel`.
- `contracts/home_page.proto`
  Stable protobuf output derived from the contract.
- `contracts/home_page.json5`
  Stable JSON5 output derived from the contract.

Run:

```bash
fvm flutter run -d chrome
```

Regenerate `freezed`:

```bash
fvm dart run build_runner build --delete-conflicting-outputs
```

Regenerate derived contract outputs:

```bash
fvm dart run fr_acdd:extract_bff_dto --format proto --input lib/page/home_page/home_page.dart --output contracts/home_page.proto
fvm dart run fr_acdd:extract_bff_dto --format json5 --input lib/page/home_page/home_page.dart --output contracts/home_page.json5
```
