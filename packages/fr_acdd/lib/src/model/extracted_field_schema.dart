class ExtractedFieldSchema {
  const ExtractedFieldSchema({
    required this.name,
    required this.wireName,
    required this.dartType,
    required this.normalizedType,
    required this.nullable,
    required this.repeated,
    this.itemType,
    this.itemNormalizedType,
    this.mapKeyType,
    this.mapKeyNormalizedType,
    this.mapValueType,
    this.mapValueNormalizedType,
    this.nestedRef,
    this.tag,
    this.defaultCode,
  });

  final String name;
  final String wireName;
  final String dartType;
  final String normalizedType;
  final bool nullable;
  final bool repeated;
  final String? itemType;
  final String? itemNormalizedType;
  final String? mapKeyType;
  final String? mapKeyNormalizedType;
  final String? mapValueType;
  final String? mapValueNormalizedType;
  final String? nestedRef;
  final int? tag;
  final String? defaultCode;
}
