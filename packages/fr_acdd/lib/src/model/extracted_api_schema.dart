class ExtractedApiSchema {
  const ExtractedApiSchema({
    required this.method,
    required this.suggestedPath,
    this.requestRefs = const [],
    this.responseRefs = const [],
    this.explicitPath = false,
  });

  final String method;
  final String suggestedPath;
  final List<String> requestRefs;
  final List<String> responseRefs;
  final bool explicitPath;
}
