class ExtractedApiSchema {
  const ExtractedApiSchema({
    required this.suggestedPath,
    required this.description,
    this.explicitPath = false,
  });

  final String suggestedPath;
  final String description;
  final bool explicitPath;
}
