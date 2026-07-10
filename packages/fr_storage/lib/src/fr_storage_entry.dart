import 'package:objectbox/objectbox.dart';

@Entity()
final class FrStorageEntry {
  FrStorageEntry({
    this.id = 0,
    required this.scopeHash,
    required this.keyHash,
    required this.payload,
  });

  @Id()
  int id;

  @Index()
  String scopeHash;

  @Index()
  String keyHash;

  String payload;
}
