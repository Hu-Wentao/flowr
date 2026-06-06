import '../enums/fr_acdd_mode.dart';

class FrAcddPage {
  const FrAcddPage({
    required this.mode,
    required this.namespace,
    this.version = 1,
  });

  final FrAcddMode mode;
  final String namespace;
  final int version;
}
