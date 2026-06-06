import '../enums/fr_acdd_dto_kind.dart';
import 'extracted_field_schema.dart';

class ExtractedDtoSchema {
  const ExtractedDtoSchema({
    required this.name,
    required this.kind,
    required this.fields,
    this.description,
  });

  final String name;
  final FrAcddDtoKind kind;
  final String? description;
  final List<ExtractedFieldSchema> fields;
}
