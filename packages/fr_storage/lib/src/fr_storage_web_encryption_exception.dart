/// Identifies the reason Web encryption could not be used.
enum FrStorageWebEncryptionErrorCode {
  insecureContext,
  secureStorageReadFailed,
  secureStorageWriteFailed,
  encryptionFailed,
  invalidStoredKey,
  keyMismatch,
  payloadCorrupted,
  modeMismatch,
}

/// A Web-specific encryption failure with actionable development guidance.
final class FrStorageWebEncryptionException implements Exception {
  const FrStorageWebEncryptionException({
    required this.code,
    required this.message,
    this.cause,
    this.causeStackTrace,
  });

  final FrStorageWebEncryptionErrorCode code;
  final String message;
  final Object? cause;
  final StackTrace? causeStackTrace;

  bool get canDisableForDevelopment => switch (code) {
    FrStorageWebEncryptionErrorCode.insecureContext ||
    FrStorageWebEncryptionErrorCode.secureStorageReadFailed ||
    FrStorageWebEncryptionErrorCode.secureStorageWriteFailed ||
    FrStorageWebEncryptionErrorCode.encryptionFailed => true,
    _ => false,
  };

  @override
  String toString() {
    final output = StringBuffer(
      'FrStorage Web encryption failed (${code.name}): $message',
    );
    if (canDisableForDevelopment) {
      output.write(
        '\nWeb encryption is enabled by default. For development only, disable '
        'it with:\n\n'
        'await FrStorage.init(\n'
        '  webOptions: const FrStorageWebOptions(\n'
        '    encryption: FrStorageWebEncryption.disabled,\n'
        '  ),\n'
        ');',
      );
    }
    if (cause != null) output.write('\nOriginal error: $cause');
    return output.toString();
  }
}
