# Figma Fill Data

Use this contract when a Figma Frame contains values that might represent user,
account, transaction, list, amount, date, or other runtime data. The Figma node
is the design evidence; do not copy a potentially sensitive sample value into
the contract.

Before implementing a Page, classify every non-copy Figma fill as `bound`,
`pending`, or `static`. Fixed labels and button copy do not need an entry.

```dart
/// Figma Data:
/// - [profile.agent.username] | Node: 18269:25314 | Kind: remote | Binding: bound | Render: ProfileModel.username | Source: UserInfoDto.username | Fixture: profile.agent.username
/// - [profile.agent.mobile] | Node: 18269:25314 | Kind: remote | Binding: pending | Render: ProfileModel.mobile | Source: TODO(figma-data): confirm approved user profile source | Fixture: profile.agent.mobile
/// - [profile.title] | Node: 18269:25314 | Kind: static-copy | Binding: static
```

Use a lower-case dotted stable ID. `Node` is the exact Figma node containing
the fill. `Kind` is `remote`, `local`, `derived`, or `static-copy`.

- `bound` requires a `XxxModel.field` render target, an approved non-TODO
  source, and a fixture ID. The View must render the declared model field.
- `pending` records the same target and fixture, but its source must contain
  `TODO(figma-data)`. It is allowed only while drafting and blocks contract
  and final validation.
- `static` is allowed only for `static-copy`; it documents an intentional fixed
  label and has no runtime data obligation.
- `- none` is allowed only after reviewing the Frame and deciding that it has
  no non-copy data fills.

Run a batch audit without changing source:

```bash
uv run --script <skill-root>/scripts/figma_fill_data.py \
  --project-root <project-root> --format markdown
```

Use `--strict` only for a project-wide cleanup gate. It reports legacy contracts
without the section, invalid declarations, and pending bindings. Do not enable
it for existing projects until their baseline has been reviewed.
