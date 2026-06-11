import 'dart:io';

import 'package:analyzer/dart/analysis/utilities.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:path/path.dart' as p;

import '../enums/fr_acdd_dto_kind.dart';
import '../enums/fr_acdd_mode.dart';
import '../model/extracted_api_schema.dart';
import '../model/extracted_contract_schema.dart';
import '../model/extracted_dto_schema.dart';
import '../model/extracted_field_schema.dart';
import 'type_normalizer.dart';

const _supportedFreezedAnnotationNames = <String>['FrAcddFreezed', 'Freezed'];

class ContractExtractor {
  ContractExtractor({TypeNormalizer? typeNormalizer})
    : _typeNormalizer = typeNormalizer ?? const TypeNormalizer();

  final TypeNormalizer _typeNormalizer;

  ExtractedContractSchema extractFromFile(String inputPath) {
    final file = File(inputPath);
    if (!file.existsSync()) {
      throw StateError('Input file does not exist: $inputPath');
    }
    return extractFromSource(
      file.readAsStringSync(),
      sourcePath: p.normalize(inputPath),
    );
  }

  ExtractedContractSchema extractFromSource(
    String source, {
    required String sourcePath,
  }) {
    final unit =
        parseString(
          content: source,
          path: sourcePath,
          throwIfDiagnostics: false,
        ).unit;

    final pageClasses = unit.declarations
        .whereType<ClassDeclaration>()
        .where(
          (declaration) =>
              _findAnnotation(declaration.metadata, 'FrAcddPage') != null,
        )
        .toList(growable: false);

    if (pageClasses.isEmpty) {
      throw StateError('No @FrAcddPage declaration found in $sourcePath.');
    }
    if (pageClasses.length > 1) {
      throw StateError(
        'Expected exactly one @FrAcddPage declaration in $sourcePath.',
      );
    }

    final pageClass = pageClasses.single;
    final pageAnnotation = _findAnnotation(pageClass.metadata, 'FrAcddPage')!;
    final modeExpression = _requireNamedArgument(
      pageAnnotation,
      'mode',
      annotationName: 'FrAcddPage',
    );
    final mode = _parseMode(modeExpression, sourcePath);
    final namespace = _readRequiredStringArgument(
      pageAnnotation,
      'namespace',
      annotationName: 'FrAcddPage',
    );
    final version =
        _readIntArgument(
          pageAnnotation,
          'version',
          annotationName: 'FrAcddPage',
        ) ??
        1;

    final docOffset =
        pageClass.metadata.isNotEmpty
            ? pageClass.metadata.first.offset
            : pageClass.offset;
    final docLines = _leadingDocCommentLines(source, docOffset);
    final routePath = _docSectionValue(docLines, 'Route');
    final figmaReference = _docSectionValue(docLines, 'Figma');
    final apiSectionLines = _docSectionItems(docLines, 'API');

    if (mode == FrAcddMode.api) {
      return ExtractedContractSchema(
        supported: false,
        mode: mode,
        namespace: namespace,
        version: version,
        source: sourcePath,
        routePath: routePath,
        figmaReference: figmaReference,
        reason: 'page uses api mode; bff dto export disabled',
        dtos: const [],
        apis: const [],
      );
    }

    final enumNames =
        unit.declarations
            .whereType<EnumDeclaration>()
            .map((declaration) => declaration.name.lexeme)
            .toSet();

    final dtoClasses = unit.declarations
        .whereType<ClassDeclaration>()
        .where(
          (declaration) =>
              _findAnnotation(declaration.metadata, 'FrAcddDto') != null,
        )
        .toList(growable: false);

    final parsedDtos = <_ParsedDtoMeta>[];
    final dtoNameByDartType = <String, String>{};
    for (final declaration in dtoClasses) {
      final annotation = _findAnnotation(declaration.metadata, 'FrAcddDto')!;
      final freezedAnnotation = _findSupportedFreezedAnnotation(
        declaration.metadata,
      );
      if (freezedAnnotation == null) {
        throw StateError(
          'Class `${declaration.name.lexeme}` is annotated with @FrAcddDto but does not declare a supported Freezed annotation. Use `@FrAcddFreezed` or `@Freezed(...)`.',
        );
      }
      final parsed = _parseDtoMeta(
        annotation,
        dartName: declaration.name.lexeme,
        sourcePath: sourcePath,
      );
      if (dtoNameByDartType.containsValue(parsed.name)) {
        throw StateError(
          'Duplicate extracted DTO name `${parsed.name}` in $sourcePath.',
        );
      }
      parsedDtos.add(parsed);
      dtoNameByDartType[parsed.dartName] = parsed.name;
    }

    final dtoTypeNames = dtoNameByDartType.keys.toSet();
    final extractedDtos = <ExtractedDtoSchema>[];
    for (final declaration in dtoClasses) {
      final parsedMeta = parsedDtos.firstWhere(
        (item) => item.dartName == declaration.name.lexeme,
      );
      final constructors = declaration.members
          .whereType<ConstructorDeclaration>()
          .where(
            (member) =>
                member.factoryKeyword != null &&
                member.redirectedConstructor != null,
          )
          .toList(growable: false);
      if (constructors.isEmpty) {
        throw StateError(
          'Class `${declaration.name.lexeme}` does not have a supported `const factory` constructor.',
        );
      }
      if (constructors.length != 1) {
        throw StateError(
          'Class `${declaration.name.lexeme}` must declare exactly one redirecting `const factory` constructor. Freezed unions are not supported for @FrAcddDto.',
        );
      }
      final constructor = constructors.single;
      if (constructor.constKeyword == null) {
        throw StateError(
          'Class `${declaration.name.lexeme}` must use `const factory` for extraction.',
        );
      }

      final fields = <ExtractedFieldSchema>[];
      for (final parameter in constructor.parameters.parameters) {
        final parsedField = _parseField(
          parameter,
          dtoTypeNames: dtoTypeNames,
          dtoNameByDartType: dtoNameByDartType,
          enumNames: enumNames,
        );
        if (parsedField == null) {
          continue;
        }
        fields.add(parsedField);
      }

      extractedDtos.add(
        ExtractedDtoSchema(
          name: parsedMeta.name,
          kind: parsedMeta.kind,
          description: parsedMeta.description,
          fields: fields,
        ),
      );
    }

    _validateNestedDtoReferences(extractedDtos);

    if (!extractedDtos.any((dto) => dto.kind == FrAcddDtoKind.root)) {
      throw StateError('At least one root DTO is required for $sourcePath.');
    }

    final apis = _buildApiSchemas(
      explicitApiLines: apiSectionLines,
      namespace: namespace,
      dtos: extractedDtos,
    );

    return ExtractedContractSchema(
      supported: true,
      mode: mode,
      namespace: namespace,
      version: version,
      source: sourcePath,
      routePath: routePath,
      figmaReference: figmaReference,
      dtos: extractedDtos,
      apis: apis,
    );
  }

  ExtractedFieldSchema? _parseField(
    FormalParameter parameter, {
    required Set<String> dtoTypeNames,
    required Map<String, String> dtoNameByDartType,
    required Set<String> enumNames,
  }) {
    final metadata = _parameterMetadata(parameter);
    final fieldAnnotation = _findAnnotation(metadata, 'FrAcddField');
    final include =
        _readBoolArgument(
          fieldAnnotation,
          'include',
          annotationName: 'FrAcddField',
        ) ??
        true;
    if (!include) {
      return null;
    }

    final name = _parameterName(parameter);
    final dartType = _parameterType(parameter);
    final normalized = _typeNormalizer.normalize(
      dartType: dartType,
      dtoNames: dtoTypeNames,
      enumNames: enumNames,
    );

    final explicitNestedRef = _readTypeArgument(
      fieldAnnotation,
      'nestedRef',
      annotationName: 'FrAcddField',
    );
    final nestedRef = _resolveDtoOutputName(
      explicitNestedRef ?? normalized.nestedRef,
      dtoNameByDartType,
    );

    return ExtractedFieldSchema(
      name: name,
      wireName:
          _readStringArgument(
            fieldAnnotation,
            'wireName',
            annotationName: 'FrAcddField',
          ) ??
          name,
      dartType: dartType,
      normalizedType: normalized.normalizedType,
      nullable: normalized.nullable,
      repeated: normalized.repeated,
      itemType: normalized.itemType,
      itemNormalizedType: normalized.itemNormalizedType,
      mapKeyType: normalized.mapKeyType,
      mapKeyNormalizedType: normalized.mapKeyNormalizedType,
      mapValueType: normalized.mapValueType,
      mapValueNormalizedType: normalized.mapValueNormalizedType,
      nestedRef: nestedRef,
      tag: _readIntArgument(
        fieldAnnotation,
        'tag',
        annotationName: 'FrAcddField',
      ),
      defaultCode: _defaultValueCode(parameter),
    );
  }

  _ParsedDtoMeta _parseDtoMeta(
    Annotation annotation, {
    required String dartName,
    required String sourcePath,
  }) {
    final kindExpression = _requireNamedArgument(
      annotation,
      'kind',
      annotationName: 'FrAcddDto',
    );
    final name =
        _readStringArgument(annotation, 'name', annotationName: 'FrAcddDto') ??
        dartName;
    if (!_identifierRegExp.hasMatch(name)) {
      throw StateError(
        'Extracted DTO name `$name` from $sourcePath must be a valid identifier.',
      );
    }
    return _ParsedDtoMeta(
      dartName: dartName,
      name: name,
      kind: _parseDtoKind(kindExpression, sourcePath),
      description: _readStringArgument(
        annotation,
        'description',
        annotationName: 'FrAcddDto',
      ),
    );
  }
}

class _ParsedDtoMeta {
  const _ParsedDtoMeta({
    required this.dartName,
    required this.name,
    required this.kind,
    this.description,
  });

  final String dartName;
  final String name;
  final FrAcddDtoKind kind;
  final String? description;
}

final RegExp _identifierRegExp = RegExp(r'^[A-Za-z_]\w*$');

Annotation? _findAnnotation(Iterable<Annotation> metadata, String name) {
  for (final annotation in metadata) {
    final annotationName = annotation.name.toSource();
    if (annotationName == name || annotationName.endsWith('.$name')) {
      return annotation;
    }
  }
  return null;
}

Annotation? _findSupportedFreezedAnnotation(Iterable<Annotation> metadata) {
  for (final name in _supportedFreezedAnnotationNames) {
    final annotation = _findAnnotation(metadata, name);
    if (annotation != null) {
      return annotation;
    }
  }
  return null;
}

Expression _requireNamedArgument(
  Annotation annotation,
  String name, {
  required String annotationName,
}) {
  final expression = _namedArgument(annotation, name);
  if (expression == null) {
    throw StateError('$annotationName is missing required argument `$name`.');
  }
  return expression;
}

Expression? _namedArgument(Annotation? annotation, String name) {
  if (annotation == null) {
    return null;
  }
  final arguments = annotation.arguments?.arguments;
  if (arguments == null) {
    return null;
  }
  for (final argument in arguments) {
    if (argument is NamedExpression && argument.name.label.name == name) {
      return argument.expression;
    }
  }
  return null;
}

String _readRequiredStringArgument(
  Annotation annotation,
  String name, {
  required String annotationName,
}) {
  final value = _readStringArgument(
    annotation,
    name,
    annotationName: annotationName,
  );
  if (value == null) {
    throw StateError('$annotationName is missing required string `$name`.');
  }
  return value;
}

String? _readStringArgument(
  Annotation? annotation,
  String name, {
  required String annotationName,
}) {
  final expression = _namedArgument(annotation, name);
  if (expression == null) {
    return null;
  }
  if (expression is! StringLiteral || expression.stringValue == null) {
    throw StateError('$annotationName.$name must be a string literal.');
  }
  return expression.stringValue;
}

int? _readIntArgument(
  Annotation? annotation,
  String name, {
  required String annotationName,
}) {
  final expression = _namedArgument(annotation, name);
  if (expression == null) {
    return null;
  }
  if (expression is! IntegerLiteral || expression.value == null) {
    throw StateError('$annotationName.$name must be an int literal.');
  }
  return expression.value;
}

bool? _readBoolArgument(
  Annotation? annotation,
  String name, {
  required String annotationName,
}) {
  final expression = _namedArgument(annotation, name);
  if (expression == null) {
    return null;
  }
  if (expression is BooleanLiteral) {
    return expression.value;
  }
  throw StateError('$annotationName.$name must be a bool literal.');
}

String? _readTypeArgument(
  Annotation? annotation,
  String name, {
  required String annotationName,
}) {
  final expression = _namedArgument(annotation, name);
  if (expression == null) {
    return null;
  }
  final value = expression.toSource().trim();
  if (value.isEmpty) {
    throw StateError('$annotationName.$name must not be empty.');
  }
  return value;
}

FrAcddMode _parseMode(Expression expression, String sourcePath) {
  final value = expression.toSource();
  if (value == 'FrAcddMode.api' || value.endsWith('.api') || value == 'api') {
    return FrAcddMode.api;
  }
  if (value == 'FrAcddMode.bffDto' ||
      value.endsWith('.bffDto') ||
      value == 'bffDto') {
    return FrAcddMode.bffDto;
  }
  throw StateError('Unsupported FrAcddPage.mode `$value` in $sourcePath.');
}

FrAcddDtoKind _parseDtoKind(Expression expression, String sourcePath) {
  final value = expression.toSource();
  if (value == 'FrAcddDtoKind.root' ||
      value.endsWith('.root') ||
      value == 'root') {
    return FrAcddDtoKind.root;
  }
  if (value == 'FrAcddDtoKind.nested' ||
      value.endsWith('.nested') ||
      value == 'nested') {
    return FrAcddDtoKind.nested;
  }
  throw StateError('Unsupported FrAcddDto.kind `$value` in $sourcePath.');
}

List<String> _leadingDocCommentLines(String source, int offset) {
  if (offset <= 0) {
    return const [];
  }
  final lines = source.substring(0, offset).split('\n');
  final collected = <String>[];
  var sawComment = false;
  for (var index = lines.length - 1; index >= 0; index -= 1) {
    final rawLine = lines[index];
    final trimmed = rawLine.trim();
    if (trimmed.isEmpty) {
      if (sawComment) {
        break;
      }
      continue;
    }
    final isDocLine =
        trimmed.startsWith('///') ||
        trimmed.startsWith('/**') ||
        trimmed.startsWith('*') ||
        trimmed.startsWith('*/');
    if (!isDocLine) {
      if (sawComment) {
        break;
      }
      continue;
    }
    sawComment = true;
    collected.add(rawLine);
  }
  if (collected.isEmpty) {
    return const [];
  }
  return collected.reversed
      .map(
        (line) =>
            line
                .replaceFirst(RegExp(r'^\s*///\s?'), '')
                .replaceFirst(RegExp(r'^\s*/\*\*\s?'), '')
                .replaceFirst(RegExp(r'^\s*\*\s?'), '')
                .replaceFirst(RegExp(r'\s*\*/\s*$'), '')
                .trim(),
      )
      .where((line) => line.isNotEmpty)
      .toList(growable: false);
}

String? _docSectionValue(List<String> lines, String label) {
  final items = _docSectionItems(lines, label);
  if (items.isEmpty) {
    return null;
  }
  return items.join(' | ');
}

List<String> _docSectionItems(List<String> lines, String label) {
  final prefix = '$label:';
  for (var index = 0; index < lines.length; index += 1) {
    final line = lines[index];
    if (!line.startsWith(prefix)) {
      continue;
    }
    final remainder = line.substring(prefix.length).trim();
    if (remainder.isNotEmpty) {
      if (remainder.toLowerCase() == 'none') {
        return const [];
      }
      return [remainder];
    }
    final collected = <String>[];
    for (var offset = index + 1; offset < lines.length; offset += 1) {
      final current = lines[offset];
      if (RegExp(r'^[A-Za-z][A-Za-z ]*:\s*').hasMatch(current)) {
        break;
      }
      final normalized = current.replaceFirst(RegExp(r'^-\s*'), '').trim();
      if (normalized.isNotEmpty) {
        collected.add(normalized);
      }
    }
    return collected;
  }
  return const [];
}

List<Annotation> _parameterMetadata(FormalParameter parameter) {
  final metadata = <Annotation>[];
  void collect(FormalParameter current) {
    metadata.addAll(current.metadata);
    if (current is DefaultFormalParameter) {
      collect(current.parameter);
    }
  }

  collect(parameter);
  return metadata;
}

FormalParameter _unwrapParameter(FormalParameter parameter) {
  var current = parameter;
  while (current is DefaultFormalParameter) {
    current = current.parameter;
  }
  return current;
}

String _parameterName(FormalParameter parameter) {
  final current = _unwrapParameter(parameter);
  if (current is SimpleFormalParameter) {
    final name = current.name?.lexeme;
    if (name != null) {
      return name;
    }
  }
  if (current is FieldFormalParameter) {
    return current.name.lexeme;
  }
  throw StateError('Unsupported factory parameter `${current.toSource()}`.');
}

String _parameterType(FormalParameter parameter) {
  final current = _unwrapParameter(parameter);
  if (current is SimpleFormalParameter) {
    return current.type?.toSource() ?? 'dynamic';
  }
  if (current is FieldFormalParameter) {
    return current.type?.toSource() ?? 'dynamic';
  }
  throw StateError('Unsupported factory parameter `${current.toSource()}`.');
}

String? _defaultValueCode(FormalParameter parameter) {
  final defaultAnnotation = _findAnnotation(
    _parameterMetadata(parameter),
    'Default',
  );
  if (defaultAnnotation != null) {
    final arguments = defaultAnnotation.arguments?.arguments;
    final argument =
        arguments != null && arguments.isNotEmpty ? arguments.first : null;
    if (argument != null) {
      return argument.toSource();
    }
  }
  if (parameter is DefaultFormalParameter && parameter.defaultValue != null) {
    return parameter.defaultValue!.toSource();
  }
  return null;
}

String? _resolveDtoOutputName(
  String? rawType,
  Map<String, String> dtoNameByDartType,
) {
  if (rawType == null) {
    return null;
  }
  return dtoNameByDartType[rawType] ?? rawType;
}

void _validateNestedDtoReferences(List<ExtractedDtoSchema> dtos) {
  final dtoNames = dtos.map((dto) => dto.name).toSet();
  for (final dto in dtos) {
    for (final field in dto.fields) {
      if (field.nestedRef == null) {
        continue;
      }
      if (!dtoNames.contains(field.nestedRef)) {
        throw StateError(
          'Field `${dto.name}.${field.name}` references unknown nested DTO `${field.nestedRef}`.',
        );
      }
    }
  }
}

List<ExtractedApiSchema> _buildApiSchemas({
  required List<String> explicitApiLines,
  required String namespace,
  required List<ExtractedDtoSchema> dtos,
}) {
  if (explicitApiLines.isNotEmpty) {
    return _dedupeApis([
      for (var index = 0; index < explicitApiLines.length; index += 1)
        _apiFromLine(
          namespace: namespace,
          line: explicitApiLines[index],
          index: index,
        ),
    ]);
  }

  final roots = dtos.where((dto) => dto.kind == FrAcddDtoKind.root).toList();
  if (roots.isEmpty) {
    return const [];
  }

  final namespacePath = _namespacePathSegment(namespace);
  final apis = <ExtractedApiSchema>[];
  for (final root in roots) {
    final branchPrefix =
        roots.length == 1
            ? '/bff/$namespacePath'
            : '/bff/$namespacePath/${_slugify(_trimModelSuffix(root.name))}';
    final splitFields = root.fields.where(_shouldSplitApiBranch).toList();
    final bootstrapFields =
        root.fields.where((field) => !_shouldSplitApiBranch(field)).toList();

    if (splitFields.isEmpty) {
      apis.add(
        ExtractedApiSchema(
          suggestedPath: branchPrefix,
          description:
              'Primary payload for ${root.name}: ${_fieldListDescription(root.fields)}.',
        ),
      );
      continue;
    }

    if (bootstrapFields.isNotEmpty) {
      apis.add(
        ExtractedApiSchema(
          suggestedPath: '$branchPrefix/bootstrap',
          description:
              'Bootstrap metadata for ${root.name}: ${_fieldListDescription(bootstrapFields)}.',
        ),
      );
    }

    for (final field in splitFields) {
      apis.add(
        ExtractedApiSchema(
          suggestedPath: '$branchPrefix/${_slugify(field.wireName)}',
          description:
              'Independent DTO branch for ${root.name}.${field.wireName}.',
        ),
      );
    }
  }

  return _dedupeApis(apis);
}

ExtractedApiSchema _apiFromLine({
  required String namespace,
  required String line,
  required int index,
}) {
  final explicitPath = _extractApiPath(line);
  return ExtractedApiSchema(
    suggestedPath:
        explicitPath ??
        '/bff/${_namespacePathSegment(namespace)}/${_fallbackApiSlug(line, index)}',
    description: line,
    explicitPath: explicitPath != null,
  );
}

List<ExtractedApiSchema> _dedupeApis(List<ExtractedApiSchema> apis) {
  final seen = <String>{};
  final deduped = <ExtractedApiSchema>[];
  for (final api in apis) {
    final key = '${api.suggestedPath}|${api.description}';
    if (seen.add(key)) {
      deduped.add(api);
    }
  }
  return deduped;
}

bool _shouldSplitApiBranch(ExtractedFieldSchema field) {
  return field.repeated || field.normalizedType == 'map';
}

String _fieldListDescription(List<ExtractedFieldSchema> fields) {
  if (fields.isEmpty) {
    return 'none';
  }
  return fields.map((field) => field.wireName).join(', ');
}

String? _extractApiPath(String line) {
  final match = RegExp(
    r'(?:[A-Z]+\s+)?(\/[-A-Za-z0-9_{}.:/?=&]+)',
  ).firstMatch(line);
  return match?.group(1);
}

String _fallbackApiSlug(String line, int index) {
  final trimmed =
      line.split(RegExp(r'\s+owns\s+|\s*->\s*|\s*:\s*|\s*;\s*')).first.trim();
  final slug = _slugify(trimmed);
  if (slug.isEmpty) {
    return 'branch-${index + 1}';
  }
  return slug;
}

String _namespacePathSegment(String namespace) {
  final parts = namespace
      .split('.')
      .map((part) => _slugify(part))
      .where((part) => part.isNotEmpty)
      .toList(growable: false);
  if (parts.isEmpty) {
    return 'dto';
  }
  return parts.join('/');
}

String _trimModelSuffix(String value) {
  return value.endsWith('Model') ? value.substring(0, value.length - 5) : value;
}

String _slugify(String value) {
  final normalized =
      value
          .replaceAllMapped(
            RegExp(r'([a-z0-9])([A-Z])'),
            (match) => '${match.group(1)}-${match.group(2)}',
          )
          .replaceAll(RegExp(r'[^A-Za-z0-9]+'), '-')
          .replaceAll(RegExp(r'-{2,}'), '-')
          .replaceAll(RegExp(r'^-|-$'), '')
          .toLowerCase();
  return normalized;
}
