# Optional Build And Packaging Optimizations

Read this reference only when the user explicitly asks to optimize Flutter
builds, command-line packaging, or dependency downloads. Do not recommend these
changes during ordinary project creation, adaptation, validation, or defect
repair.

Treat every item as an option, not a scaffold default. Inspect the target
project first, explain the expected benefit and compatibility boundary, and
apply only the options the user authorizes.

## Package Metadata

- Prefer Flutter's `--build-name` and `--build-number` as the package version
  authority when a release command already supplies them.
- Read the installed package metadata at runtime only when application code
  needs to display or transmit that version. Do not duplicate the same values
  into custom `dart-define` keys.
- Preserve the target project's current version unless the user explicitly
  authorizes a version change.

## Build-Time Parameters

- Use `dart-define` only for non-sensitive values that genuinely differ by
  build and already have an authoritative consumer.
- Omit optional request headers when their build-time value is empty.
- Never put credentials, private keys, session tokens, user identities, or
  mutable runtime state into build-time parameters.
- Do not invent a routing, debug, or device-token parameter merely as an
  optimization; add one only when the target protocol already defines it.

## CocoaPods Sources

- Consider an explicit public CocoaPods CDN or public mirror only when the user
  asks to improve dependency resolution and the current source is measurably
  slow or unavailable.
- Verify the source is publicly reachable, current, and compatible with every
  required pod before changing the Podfile.
- Preserve existing private spec repositories and their required precedence.

## Gradle Distribution Mirrors

- When the user asks to optimize Gradle downloads, search the web at that time
  for currently maintained public mirror nodes. Prefer authoritative or
  well-documented HTTPS endpoints and cite the source used for the
  recommendation.
- Change only the distribution URL base when possible. Preserve the project's
  exact Gradle version and distribution type, including the `-bin` versus
  `-all` suffix.
- Never copy, disclose, or recommend a private project mirror, internal host,
  private IP address, credential-bearing URL, or organization-only path.
- Keep the original public distribution URL available as the rollback value,
  and verify the selected archive's integrity before relying on the mirror.

## Dependency Repository Order

- Consider repository reordering only after measuring resolution latency or
  failures. Keep repositories required for plugins and artifacts.
- Put a faster verified public source before a slower fallback only when
  artifact identity and trust guarantees remain equivalent.
- Re-run dependency resolution on every supported platform after changing
  repository precedence.

## Platform Configuration Cleanup

- Remove stale iOS, Android, or desktop dependency configuration only after
  proving the referenced dependency is absent from manifests, generated
  integration files, and native build settings.
- Do not recommend deleting a named library or build setting solely because
  another project removed it.

## Verification

- Keep package-metadata unit tests independent of the target project's current
  version. Assert that supplied metadata maps to application configuration
  rather than hard-coding the release version in the test.
- Test configured and empty optional build values separately.
- Run dependency resolution, platform configuration syntax checks, focused
  tests, and the repository analyzer. Run a real platform build when signing,
  network access, and toolchain availability permit it.
- Report mirror reachability, signing, and private-network checks that were not
  exercised; do not infer them from static validation.
