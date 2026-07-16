## Unreleased

- Add an IndexedDB backend for Flutter Web with encryption enabled by default.
- Allow Web encryption to be disabled explicitly for non-sensitive development
  data without changing native encryption behavior.
- Add actionable Web encryption exceptions without automatic plaintext
  fallback.

## 0.1.0 2026-07-10

- Add encrypted Hive-style `FrStorage -> FrBox` string CRUD backed by ObjectBox.
- Add a static default owner and initialized multi-instance API.
- Add authenticated payload encryption and keyed indexes.
