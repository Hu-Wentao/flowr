// The package supports analyzer 6.x-10.x. These legacy AST accessors are the
// common compatibility surface across that range.
// ignore_for_file: deprecated_member_use

import 'dart:io';

import 'package:analyzer/dart/analysis/utilities.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:analyzer/dart/ast/token.dart';
import 'package:path/path.dart' as p;

import '../enums/fr_acdd_dto_kind.dart';
import '../enums/fr_acdd_mode.dart';
import '../model/extracted_api_schema.dart';
import '../model/extracted_contract_schema.dart';
import '../model/extracted_dto_schema.dart';
import '../model/extracted_field_schema.dart';
import 'type_normalizer.dart';

const _supportedFreezedAnnotationNames = <String>[
  'FrAcddFreezed',
  'FrAcddFreezedJSON',
  'Freezed',
];

class _SourceUnit {
  const _SourceUnit({required this.source, required this.unit});

  factory _SourceUnit.parse(String source, {required String sourcePath}) {
    return _SourceUnit(
      source: source,
      unit:
          parseString(
            content: source,
            path: sourcePath,
            throwIfDiagnostics: false,
          ).unit,
    );
  }

  final String source;
  final CompilationUnit unit;
}

bool _isGeneratedPart(String uri) {
  return uri.endsWith('.freezed.dart') || uri.endsWith('.g.dart');
}

({bool isUri, String value})? _partOfReference(CompilationUnit unit) {
  final directives = unit.directives.whereType<PartOfDirective>().toList();
  if (directives.length != 1) {
    return null;
  }
  final source = directives.single.toSource().trim();
  final uri = RegExp(
    r'''^part\s+of\s+['"]([^'"]+)['"]\s*;$''',
  ).firstMatch(source)?.group(1);
  if (uri != null) {
    return (isUri: true, value: uri);
  }
  final name = RegExp(
    r'^part\s+of\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;$',
  ).firstMatch(source)?.group(1);
  return name == null ? null : (isUri: false, value: name);
}

String? _libraryName(CompilationUnit unit) {
  for (final directive in unit.directives) {
    final name = RegExp(
      r'^library\s+([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;$',
    ).firstMatch(directive.toSource().trim())?.group(1);
    if (name != null) {
      return name;
    }
  }
  return null;
}

List<String> _documentationCommentSources(CompilationUnit unit) {
  final sources = <String>[];
  var token = unit.beginToken;
  while (true) {
    Token? comment = token.precedingComments;
    var lineComments = <String>[];
    void flushLineComments() {
      if (lineComments.isNotEmpty) {
        sources.add(lineComments.join('\n'));
        lineComments = <String>[];
      }
    }

    while (comment != null) {
      final lexeme = comment.lexeme.trimLeft();
      if (lexeme.startsWith('///')) {
        lineComments.add(comment.lexeme);
      } else {
        flushLineComments();
        if (lexeme.startsWith('/**')) {
          sources.add(comment.lexeme);
        }
      }
      comment = comment.next;
    }
    flushLineComments();
    if (token.isEof || token.next == token) {
      break;
    }
    token = token.next!;
  }
  return sources;
}

class ContractExtractor {
  ContractExtractor({TypeNormalizer? typeNormalizer})
    : _typeNormalizer = typeNormalizer ?? const TypeNormalizer();

  final TypeNormalizer _typeNormalizer;

  ExtractedContractSchema extractFromFile(String inputPath) {
    final shellFile = File(inputPath);
    if (!shellFile.existsSync()) {
      throw StateError('Input file does not exist: $inputPath');
    }

    final shellPath = p.normalize(inputPath);
    final shell = _SourceUnit.parse(
      shellFile.readAsStringSync(),
      sourcePath: shellPath,
    );
    if (shell.unit.directives.whereType<PartOfDirective>().isNotEmpty) {
      throw StateError(
        'The --input path must be the Dart library shell, not a `part of` file: '
        '$shellPath. Pass the file that declares this part with `part ...;`.',
      );
    }

    final units = <_SourceUnit>[shell];
    final shellLibraryName = _libraryName(shell.unit);
    final seenPartUris = <String>{};
    for (final directive in shell.unit.directives.whereType<PartDirective>()) {
      final uri = directive.uri.stringValue;
      if (uri == null || uri.trim().isEmpty) {
        throw StateError(
          'Library part URI must be a string literal in $shellPath.',
        );
      }
      if (!seenPartUris.add(uri)) {
        throw StateError(
          'Duplicate Dart part `$uri` declared by library shell $shellPath.',
        );
      }
      if (_isGeneratedPart(uri)) {
        continue;
      }
      final partPath = p.normalize(p.join(shellFile.parent.path, uri));
      final partFile = File(partPath);
      if (!partFile.existsSync()) {
        throw StateError(
          'Authored Dart part `$uri` declared by $shellPath does not exist at '
          '$partPath. Generated `.freezed.dart` and `.g.dart` parts may be '
          'absent, but authored parts are required.',
        );
      }
      final part = _SourceUnit.parse(
        partFile.readAsStringSync(),
        sourcePath: partPath,
      );
      final partOf = _partOfReference(part.unit);
      if (partOf == null) {
        throw StateError(
          'Authored Dart part `$partPath` must declare exactly one URI or '
          'library-name `part of` for the library shell $shellPath.',
        );
      }
      if (partOf.isUri) {
        final declaredShell = p.normalize(
          p.join(partFile.parent.path, partOf.value),
        );
        if (!p.equals(declaredShell, shellPath)) {
          throw StateError(
            'Authored Dart part `$partPath` belongs to `${partOf.value}`, not '
            'library shell $shellPath.',
          );
        }
      } else if (shellLibraryName == null || partOf.value != shellLibraryName) {
        throw StateError(
          'Authored Dart part `$partPath` belongs to library `${partOf.value}`, '
          'not `${shellLibraryName ?? '<unnamed>'}` from shell $shellPath.',
        );
      }
      units.add(part);
    }
    return _extractFromUnits(units, libraryPath: shellPath);
  }

  ExtractedContractSchema extractFromSource(
    String source, {
    required String sourcePath,
  }) {
    final normalizedPath = p.normalize(sourcePath);
    final unit = _SourceUnit.parse(source, sourcePath: normalizedPath);
    if (unit.unit.directives.whereType<PartOfDirective>().isNotEmpty) {
      throw StateError(
        'ContractExtractor requires a Dart library shell, not a `part of` '
        'source: $normalizedPath.',
      );
    }
    return _extractFromUnits([unit], libraryPath: normalizedPath);
  }

  ExtractedContractSchema _extractFromUnits(
    List<_SourceUnit> units, {
    required String libraryPath,
  }) {
    final declarations = [for (final unit in units) ...unit.unit.declarations];
    final pageClasses = declarations
        .whereType<ClassDeclaration>()
        .where(
          (declaration) =>
              _findAnnotation(declaration.metadata, 'FrAcddPage') != null,
        )
        .toList(growable: false);

    if (pageClasses.isEmpty) {
      throw StateError(
        'No @FrAcddPage declaration found in library $libraryPath or its '
        'authored parts.',
      );
    }
    if (pageClasses.length > 1) {
      throw StateError(
        'Expected exactly one @FrAcddPage declaration across library '
        '$libraryPath and its authored parts.',
      );
    }

    final pageClass = pageClasses.single;
    final pageAnnotation = _findAnnotation(pageClass.metadata, 'FrAcddPage')!;
    final modeExpression = _requireNamedArgument(
      pageAnnotation,
      'mode',
      annotationName: 'FrAcddPage',
    );
    final mode = _parseMode(modeExpression, libraryPath);
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

    final docBlocks = [
      for (final unit in units)
        for (final comment in _documentationCommentSources(unit.unit))
          ..._documentationBlocks(comment),
    ];
    final canonicalBffSections = _sectionOccurrences(docBlocks, 'BFF-UI-API');
    final legacyBffSections = _sectionOccurrences(docBlocks, 'BFF-API');
    if (canonicalBffSections.isNotEmpty && legacyBffSections.isNotEmpty) {
      throw StateError(
        'Library $libraryPath must not mix canonical `BFF-UI-API:` with legacy '
        '`BFF-API:`. Rename the legacy section to `BFF-UI-API:`.',
      );
    }
    final routePath = _uniqueDocSectionValue(docBlocks, 'Route', libraryPath);
    final figmaReference = _uniqueDocSectionValue(
      docBlocks,
      'Figma',
      libraryPath,
    );
    final apiLabel =
        mode == FrAcddMode.bff
            ? legacyBffSections.isNotEmpty
                ? 'BFF-API'
                : 'BFF-UI-API'
            : 'API';
    final apiSectionDeclared =
        _sectionOccurrences(docBlocks, apiLabel).isNotEmpty;
    final apiSectionBlocks = _uniqueDocSectionBlocks(
      docBlocks,
      apiLabel,
      libraryPath,
    );

    if (mode == FrAcddMode.api) {
      return ExtractedContractSchema(
        supported: false,
        mode: mode,
        namespace: namespace,
        version: version,
        source: libraryPath,
        routePath: routePath,
        figmaReference: figmaReference,
        reason: 'page uses api mode; bff export disabled',
        dtos: const [],
        apis: const [],
      );
    }

    final enumNames =
        declarations
            .whereType<EnumDeclaration>()
            .map((declaration) => declaration.name.lexeme)
            .toSet();

    final dtoClasses = declarations
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
          'Class `${declaration.name.lexeme}` is annotated with @FrAcddDto but does not declare a supported Freezed annotation. Use `@FrAcddFreezed`, `@FrAcddFreezedJSON`, or `@Freezed(...)`.',
        );
      }
      final parsed = _parseDtoMeta(
        annotation,
        dartName: declaration.name.lexeme,
        sourcePath: libraryPath,
      );
      if (dtoNameByDartType.containsValue(parsed.name)) {
        throw StateError(
          'Duplicate extracted DTO name `${parsed.name}` in $libraryPath.',
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
      throw StateError('At least one root DTO is required for $libraryPath.');
    }

    final apis = _buildApiSchemas(
      explicitApis: [
        for (var index = 0; index < apiSectionBlocks.length; index += 1)
          _apiFromBlock(
            namespace: namespace,
            sourcePath: libraryPath,
            block: apiSectionBlocks[index],
            index: index,
          ),
      ],
      namespace: namespace,
      sourcePath: libraryPath,
      dtos: extractedDtos,
      inferDefaults: !apiSectionDeclared,
    );
    _validateBffNaming(extractedDtos, apis, libraryPath);

    return ExtractedContractSchema(
      supported: true,
      mode: mode,
      namespace: namespace,
      version: version,
      source: libraryPath,
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

void _validateBffNaming(
  List<ExtractedDtoSchema> dtos,
  List<ExtractedApiSchema> apis,
  String sourcePath,
) {
  final boundaryNames = <String>{};
  for (final api in apis) {
    for (final name in api.requestRefs) {
      boundaryNames.add(name);
      if (!name.endsWith('BffReq')) {
        throw StateError(
          'BFF request DTO `$name` in $sourcePath must use the `XxxBffReq` suffix.',
        );
      }
    }
    for (final name in api.responseRefs) {
      boundaryNames.add(name);
      if (!name.endsWith('BffRsp')) {
        throw StateError(
          'BFF response DTO `$name` in $sourcePath must use the `XxxBffRsp` suffix.',
        );
      }
    }
  }
  for (final dto in dtos) {
    if (!boundaryNames.contains(dto.name) && !dto.name.endsWith('Dto')) {
      throw StateError(
        'Internal BFF DTO `${dto.name}` in $sourcePath must use the `XxxDto` suffix.',
      );
    }
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
  if (value == 'FrAcddMode.bff' || value.endsWith('.bff') || value == 'bff') {
    return FrAcddMode.bff;
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

List<List<String>> _documentationBlocks(String source) {
  final blocks = <List<String>>[];
  final lines = source.split('\n');
  List<String>? current;
  var inBlockComment = false;

  void flush() {
    if (current != null && current!.isNotEmpty) {
      blocks.add(List.unmodifiable(current!));
    }
    current = null;
  }

  for (final rawLine in lines) {
    final trimmed = rawLine.trim();
    if (trimmed.startsWith('///')) {
      if (inBlockComment) {
        flush();
        inBlockComment = false;
      }
      current ??= <String>[];
      final value = trimmed.replaceFirst(RegExp(r'^///\s?'), '').trim();
      if (value.isNotEmpty) {
        current!.add(value);
      }
      continue;
    }
    if (trimmed.startsWith('/**')) {
      flush();
      inBlockComment = true;
      current = <String>[];
      final value =
          trimmed
              .replaceFirst(RegExp(r'^/\*\*\s?'), '')
              .replaceFirst(RegExp(r'\s*\*/$'), '')
              .trim();
      if (value.isNotEmpty) {
        current!.add(value);
      }
      if (trimmed.endsWith('*/')) {
        flush();
        inBlockComment = false;
      }
      continue;
    }
    if (inBlockComment) {
      final value =
          trimmed
              .replaceFirst(RegExp(r'^\*\s?'), '')
              .replaceFirst(RegExp(r'\s*\*/$'), '')
              .trim();
      if (value.isNotEmpty) {
        current!.add(value);
      }
      if (trimmed.endsWith('*/')) {
        flush();
        inBlockComment = false;
      }
      continue;
    }
    flush();
  }
  flush();
  return blocks;
}

List<List<String>> _sectionOccurrences(
  List<List<String>> docBlocks,
  String label,
) {
  final prefix = '$label:';
  final occurrences = <List<String>>[];
  for (final block in docBlocks) {
    for (var index = 0; index < block.length; index += 1) {
      if (block[index].startsWith(prefix)) {
        occurrences.add(block.sublist(index));
      }
    }
  }
  return occurrences;
}

String? _uniqueDocSectionValue(
  List<List<String>> docBlocks,
  String label,
  String libraryPath,
) {
  final occurrences = _sectionOccurrences(docBlocks, label);
  if (occurrences.length > 1) {
    throw StateError(
      'Expected at most one `$label:` section across library $libraryPath and '
      'its authored parts; found ${occurrences.length}.',
    );
  }
  return occurrences.isEmpty
      ? null
      : _docSectionValue(occurrences.single, label);
}

List<List<String>> _uniqueDocSectionBlocks(
  List<List<String>> docBlocks,
  String label,
  String libraryPath,
) {
  final occurrences = _sectionOccurrences(docBlocks, label);
  if (occurrences.length > 1) {
    throw StateError(
      'Expected at most one `$label:` section across library $libraryPath and '
      'its authored parts; found ${occurrences.length}.',
    );
  }
  return occurrences.isEmpty
      ? const []
      : _docSectionBlocks(occurrences.single, label);
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
      if (RegExp(r'^[A-Za-z][A-Za-z -]*:\s*').hasMatch(current)) {
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

List<List<String>> _docSectionBlocks(List<String> lines, String label) {
  final prefix = '$label:';
  for (var index = 0; index < lines.length; index += 1) {
    final line = lines[index];
    if (!line.startsWith(prefix)) {
      continue;
    }
    final remainder = line.substring(prefix.length).trim();
    if (remainder.isNotEmpty) {
      if (remainder.toLowerCase() == 'none' || remainder == '-') {
        return const [];
      }
      return [
        [remainder],
      ];
    }
    final blocks = <List<String>>[];
    List<String>? current;
    for (var offset = index + 1; offset < lines.length; offset += 1) {
      final currentLine = lines[offset];
      if (RegExp(r'^[A-Za-z][A-Za-z -]*:\s*').hasMatch(currentLine)) {
        break;
      }
      final normalized = currentLine.replaceFirst(RegExp(r'^-\s*'), '').trim();
      if (normalized.isEmpty) {
        continue;
      }
      final startsApiBlock = RegExp(
        r'^(GET|POST|PUT|PATCH|DELETE)\s+\S+',
      ).hasMatch(normalized);
      if (startsApiBlock || currentLine.startsWith('- ')) {
        current = [normalized];
        blocks.add(current);
        continue;
      }
      if (current == null) {
        current = [normalized];
        blocks.add(current);
        continue;
      }
      current.add(normalized);
    }
    return blocks;
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
  required List<ExtractedApiSchema> explicitApis,
  required String namespace,
  required String sourcePath,
  required List<ExtractedDtoSchema> dtos,
  required bool inferDefaults,
}) {
  if (explicitApis.isNotEmpty) {
    return _dedupeApis(explicitApis);
  }
  if (!inferDefaults) {
    return const [];
  }

  final roots = dtos.where((dto) => dto.kind == FrAcddDtoKind.root).toList();
  if (roots.isEmpty) {
    return const [];
  }

  final namespacePath = _defaultApiBasePath(
    sourcePath: sourcePath,
    namespace: namespace,
  );
  final apis = <ExtractedApiSchema>[];
  for (final root in roots) {
    final branchPrefix =
        roots.length == 1
            ? namespacePath
            : '$namespacePath/${_slugify(_trimBffSuffix(root.name))}';
    final splitFields = root.fields.where(_shouldSplitApiBranch).toList();
    final bootstrapFields =
        root.fields.where((field) => !_shouldSplitApiBranch(field)).toList();

    if (splitFields.isEmpty) {
      apis.add(
        ExtractedApiSchema(
          method: 'GET',
          suggestedPath: branchPrefix,
          responseRefs: [root.name],
        ),
      );
      continue;
    }

    if (bootstrapFields.isNotEmpty) {
      apis.add(
        ExtractedApiSchema(
          method: 'GET',
          suggestedPath: '$branchPrefix/bootstrap',
          responseRefs: [root.name],
        ),
      );
    }

    for (final field in splitFields) {
      apis.add(
        ExtractedApiSchema(
          method: 'GET',
          suggestedPath: '$branchPrefix/${_slugify(field.wireName)}',
          responseRefs:
              field.nestedRef == null ? [root.name] : [field.nestedRef!],
        ),
      );
    }
  }

  return _dedupeApis(apis);
}

ExtractedApiSchema _apiFromBlock({
  required String namespace,
  required String sourcePath,
  required List<String> block,
  required int index,
}) {
  final header = block.first.trim();
  final refs = <String>[
    for (final line in block)
      for (final match in RegExp(r'\[([A-Za-z_]\w*)\]').allMatches(line))
        match.group(1)!,
  ];
  final explicitPath = _extractApiPath(header);
  final basePath = _defaultApiBasePath(
    sourcePath: sourcePath,
    namespace: namespace,
  );
  return ExtractedApiSchema(
    method: _extractApiMethod(header) ?? 'GET',
    suggestedPath:
        explicitPath ?? '$basePath/${_fallbackApiSlug(header, index)}',
    requestRefs: refs.length >= 2 ? [refs.first] : const <String>[],
    responseRefs:
        refs.length >= 2
            ? refs.sublist(1)
            : refs.length == 1
            ? [refs.first]
            : const <String>[],
    explicitPath: explicitPath != null,
  );
}

List<ExtractedApiSchema> _dedupeApis(List<ExtractedApiSchema> apis) {
  final seen = <String>{};
  final deduped = <ExtractedApiSchema>[];
  for (final api in apis) {
    final key =
        '${api.method}|${api.suggestedPath}|'
        '${api.requestRefs.join(",")}|${api.responseRefs.join(",")}';
    if (seen.add(key)) {
      deduped.add(api);
    }
  }
  return deduped;
}

bool _shouldSplitApiBranch(ExtractedFieldSchema field) {
  return field.repeated ||
      field.normalizedType == 'map' ||
      (field.normalizedType == 'object' && field.nestedRef != null);
}

String? _extractApiPath(String line) {
  final match = RegExp(
    r'(<BASE>\/[-A-Za-z0-9_{}.:/?=&]+|\/[-A-Za-z0-9_{}.:/?=&]+)',
  ).firstMatch(line);
  return match?.group(1);
}

String? _extractApiMethod(String line) {
  final match = RegExp(
    r'^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b',
  ).firstMatch(line.trim());
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

String _defaultApiBasePath({
  required String sourcePath,
  required String namespace,
}) {
  final normalized = p.posix.normalize(sourcePath.replaceAll('\\', '/'));
  final segments = p.posix.split(normalized);
  final libIndex = segments.lastIndexOf('lib');
  if (libIndex != -1) {
    final pageIndex =
        libIndex + 1 < segments.length && segments[libIndex + 1] == 'page'
            ? libIndex + 1
            : libIndex + 2 < segments.length &&
                segments[libIndex + 1] == 'src' &&
                segments[libIndex + 2] == 'page'
            ? libIndex + 2
            : -1;
    if (pageIndex != -1 && segments.length - 1 > pageIndex) {
      final dirSegments = segments.sublist(pageIndex + 1, segments.length - 1);
      if (dirSegments.isNotEmpty) {
        return '<BASE>/${dirSegments.map(_slugify).join('/')}';
      }
    }
  }
  return '<BASE>/${_namespacePathSegment(namespace)}';
}

String _trimBffSuffix(String value) {
  for (final suffix in const ['BffReq', 'BffRsp', 'Dto']) {
    if (value.endsWith(suffix)) {
      return value.substring(0, value.length - suffix.length);
    }
  }
  return value;
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
