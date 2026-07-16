/// Controls whether values stored by the Web backend are encrypted.
enum FrStorageWebEncryption { enabled, disabled }

/// Web-only configuration for [FrStorage].
///
/// Native platforms ignore these options and continue to use encrypted
/// ObjectBox storage.
final class FrStorageWebOptions {
  const FrStorageWebOptions({this.encryption = FrStorageWebEncryption.enabled});

  final FrStorageWebEncryption encryption;

  bool get encryptionEnabled => encryption == FrStorageWebEncryption.enabled;
}
