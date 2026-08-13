# Application Information Check

Inspect the current Flutter project and report which configuration is still
missing compared with a common complete Android/iOS application. This task is
read-only. Do not create placeholder values or change platform configuration.

## Scope

Inspect and report all six items:

1. Package identifiers
2. Application names
3. Android and iOS icons
4. Developer identities
5. Minimum supported system versions
6. Push notification configuration

Use one of these statuses for each platform-specific result:

- `configured`: repository evidence is present and internally consistent.
- `missing`: a required file or value is absent, empty, or still a template.
- `unverified`: repository files cannot prove the external account,
  certificate, entitlement, or console-side setup.
- `not applicable`: the project does not target that platform or the related
  optional capability is not used.

Do not interpret the presence of a local file as proof that an external
developer account, certificate, store registration, or push service is valid.
Do not print secrets, certificate contents, keystore passwords, or service
credentials.

## Inspection

### 1. Package Identifiers

- Android: inspect `android/app/build.gradle`,
  `android/app/build.gradle.kts`, and referenced Gradle properties for the
  effective `applicationId`. Also record `namespace` when present and flag an
  unintended mismatch or a template identifier such as `com.example.*`.
- iOS: inspect `ios/Runner.xcodeproj/project.pbxproj` and build settings for
  `PRODUCT_BUNDLE_IDENTIFIER`. Check every relevant build configuration and
  flag missing, inconsistent, or template identifiers.

Report Android and iOS separately even when they intentionally use related
identifiers.

### 2. Application Names

- Android: resolve `android:label` from `android/app/src/main/AndroidManifest.xml`
  through any referenced string resource. Flag `${applicationName}` only when
  it is being mistaken for the user-visible application label.
- iOS: inspect `CFBundleDisplayName` and `CFBundleName` in
  `ios/Runner/Info.plist`, including build-setting substitutions and localized
  `InfoPlist.strings` values when present.

Flag missing, blank, obviously generated, or inconsistent user-visible names.

### 3. Application Icons

- Android: verify launcher icon resources exist for the manifest's icon and
  round-icon references. Inspect density-specific `mipmap-*` files and any
  adaptive icon XML under `mipmap-anydpi-v26`; flag default Flutter/template
  artwork when it is identifiable.
- iOS: inspect `ios/Runner/Assets.xcassets/AppIcon.appiconset/Contents.json`.
  Verify referenced image files exist and required phone icon slots are not
  empty; flag default Flutter/template artwork when it is identifiable.

The presence of an asset catalog or directory alone is not sufficient.

### 4. Developer Identities

- iOS: inspect `DEVELOPMENT_TEAM`, signing style, signing certificate, and
  provisioning-profile settings in the Xcode project. Report repository
  evidence, then mark the Apple Developer account, certificate validity, and
  provisioning access `unverified` unless an authorized external check proves
  them.
- Android: inspect release signing configuration and safe references to a
  keystore or environment-backed credentials. Never read or reveal secret
  values. Mark the Google Play developer account and upload/app-signing access
  `unverified` unless an authorized external check proves them.

Absence of release signing evidence is `missing`; external account ownership
that cannot be checked from the repository is `unverified`.

### 5. Minimum Supported Versions

- iOS: determine the effective `IPHONEOS_DEPLOYMENT_TARGET` from the Xcode
  project, xcconfig files, and `ios/Podfile` platform declaration. Report
  inconsistent values instead of selecting one silently.
- Android: determine the effective `minSdk` or `minSdkVersion` from the app
  Gradle configuration and referenced properties. When it delegates to a
  Flutter or shared Gradle value, resolve that value if possible; otherwise
  report it as indirect and `unverified`.

Report the actual values. Do not decide whether to raise or lower them during
this task.

### 6. Push Notification Configuration

First inspect dependencies, initialization code, native manifests,
entitlements, and service usage to determine whether push notifications are
used and which provider owns them.

- If Firebase Messaging is used, require the applicable platform files:
  `android/app/google-services.json` for Android and
  `ios/Runner/GoogleService-Info.plist` for iOS. Also verify the Android Google
  Services plugin, iOS target membership or project reference, Firebase
  initialization, and `aps-environment` entitlement/capability evidence.
- If another push provider is used, report its equivalent native configuration
  and entitlement evidence.
- If no push implementation or declared requirement is found, report push as
  `not applicable` and state the evidence used for that conclusion. Do not
  label it configured.

Treat checked-in example files, empty placeholders, and files for the wrong
bundle/application identifier as `missing` or inconsistent, not configured.

## Output

Start with a concise completeness summary, then use a table with these columns:

| Item | Android | iOS | Evidence | Missing or next verification |
| --- | --- | --- | --- | --- |

Include one row for each of the six scope items. In the developer-identity row,
separate repository signing evidence from external account/certificate status.
End with:

1. Missing repository configuration that can be implemented.
2. External developer-account, certificate, store, or service checks that
   require user access.
3. Explicitly `not applicable` items and why.

If nothing is missing, say so without claiming that externally unverified
accounts or certificates are valid.
