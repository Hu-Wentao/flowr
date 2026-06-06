import '../enums/fr_acdd_dto_kind.dart';

class FrAcddDto {
  const FrAcddDto({required this.kind, this.name, this.description});

  final FrAcddDtoKind kind;
  final String? name;
  final String? description;
}
