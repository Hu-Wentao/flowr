class NormalizedTypeDescriptor {
  const NormalizedTypeDescriptor({
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
  });

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
}

class TypeNormalizer {
  const TypeNormalizer();

  NormalizedTypeDescriptor normalize({
    required String dartType,
    required Set<String> dtoNames,
    required Set<String> enumNames,
  }) {
    final compactType = dartType.replaceAll(RegExp(r'\s+'), '');
    final nullable = compactType.endsWith('?');
    final baseType =
        nullable
            ? compactType.substring(0, compactType.length - 1)
            : compactType;

    if (_isGeneric(baseType, 'List')) {
      final itemType = _genericArgs(baseType).single;
      return NormalizedTypeDescriptor(
        normalizedType: 'list',
        nullable: nullable,
        repeated: true,
        itemType: itemType,
        itemNormalizedType: _classifyScalarOrObject(
          itemType,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
        nestedRef: _objectRefForType(
          itemType,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
      );
    }

    if (_isGeneric(baseType, 'Set')) {
      final itemType = _genericArgs(baseType).single;
      return NormalizedTypeDescriptor(
        normalizedType: 'set',
        nullable: nullable,
        repeated: true,
        itemType: itemType,
        itemNormalizedType: _classifyScalarOrObject(
          itemType,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
        nestedRef: _objectRefForType(
          itemType,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
      );
    }

    if (_isGeneric(baseType, 'Map')) {
      final args = _genericArgs(baseType);
      if (args.length != 2) {
        throw StateError('Unsupported map type `$dartType`.');
      }
      return NormalizedTypeDescriptor(
        normalizedType: 'map',
        nullable: nullable,
        repeated: false,
        mapKeyType: args.first,
        mapKeyNormalizedType: _classifyScalarOrObject(
          args.first,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
        mapValueType: args.last,
        mapValueNormalizedType: _classifyScalarOrObject(
          args.last,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
        nestedRef: _objectRefForType(
          args.last,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ),
      );
    }

    final normalizedType = _classifyScalarOrObject(
      baseType,
      dtoNames: dtoNames,
      enumNames: enumNames,
    );
    return NormalizedTypeDescriptor(
      normalizedType: normalizedType,
      nullable: nullable,
      repeated: false,
      nestedRef: _objectRefForType(
        baseType,
        dtoNames: dtoNames,
        enumNames: enumNames,
      ),
    );
  }

  String _classifyScalarOrObject(
    String rawType, {
    required Set<String> dtoNames,
    required Set<String> enumNames,
  }) {
    final type = rawType.replaceAll(RegExp(r'\s+'), '').replaceFirst('?', '');
    switch (type) {
      case 'String':
        return 'string';
      case 'int':
        return 'int';
      case 'double':
        return 'double';
      case 'num':
        return 'num';
      case 'bool':
        return 'bool';
      case 'DateTime':
        return 'datetime';
      default:
        if (enumNames.contains(type)) {
          return 'enum';
        }
        if (dtoNames.contains(type)) {
          return 'object';
        }
        return 'object';
    }
  }

  String? _objectRefForType(
    String rawType, {
    required Set<String> dtoNames,
    required Set<String> enumNames,
  }) {
    final type = rawType.replaceAll(RegExp(r'\s+'), '').replaceFirst('?', '');
    if (enumNames.contains(type)) {
      return null;
    }
    if (_classifyScalarOrObject(
          type,
          dtoNames: dtoNames,
          enumNames: enumNames,
        ) ==
        'object') {
      return type;
    }
    return null;
  }

  bool _isGeneric(String type, String base) {
    return type.startsWith('$base<') && type.endsWith('>');
  }

  List<String> _genericArgs(String type) {
    final start = type.indexOf('<');
    if (start == -1 || !type.endsWith('>')) {
      return const [];
    }
    final raw = type.substring(start + 1, type.length - 1);
    final parts = <String>[];
    var buffer = StringBuffer();
    var depth = 0;
    for (final char in raw.split('')) {
      if (char == '<') {
        depth += 1;
      } else if (char == '>') {
        depth -= 1;
      } else if (char == ',' && depth == 0) {
        parts.add(buffer.toString());
        buffer = StringBuffer();
        continue;
      }
      buffer.write(char);
    }
    if (buffer.isNotEmpty) {
      parts.add(buffer.toString());
    }
    return parts.map((part) => part.trim()).toList(growable: false);
  }
}
