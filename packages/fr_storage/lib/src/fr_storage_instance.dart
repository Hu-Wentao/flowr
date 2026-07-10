import 'fr_box.dart';

/// An independently configured, initialized storage owner.
abstract interface class FrStorageInstance {
  bool get isInitialized;

  FrBox box(String name);

  Future<void> close();
}
