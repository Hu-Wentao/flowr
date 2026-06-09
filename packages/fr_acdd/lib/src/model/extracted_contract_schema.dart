import '../enums/fr_acdd_mode.dart';
import 'extracted_api_schema.dart';
import 'extracted_dto_schema.dart';

class ExtractedContractSchema {
  const ExtractedContractSchema({
    required this.supported,
    required this.mode,
    required this.namespace,
    required this.version,
    required this.source,
    required this.dtos,
    required this.apis,
    this.routePath,
    this.figmaReference,
    this.reason,
  });

  final bool supported;
  final FrAcddMode mode;
  final String namespace;
  final int version;
  final String source;
  final String? routePath;
  final String? figmaReference;
  final String? reason;
  final List<ExtractedDtoSchema> dtos;
  final List<ExtractedApiSchema> apis;
}
