import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  group('library shell extraction', () {
    test('aggregates authored parts and skips missing generated parts', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_library_');
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync(r'''
import 'package:fr_acdd/fr_acdd.dart';
part 'orders.c.dart';
part 'orders.v.dart';
part 'orders.freezed.dart';
part 'orders.g.dart';
''');
      File(p.join(root.path, 'orders.c.dart')).writeAsStringSync(r'''
/// Figma: https://www.figma.com/design/orders
/// Route: /orders
/// BFF-API:
/// GET <BASE>/orders
/// [OrdersBffReq], [OrdersBffRsp]
/// POST <BASE>/orders/confirm
/// [ConfirmOrderBffReq], [ConfirmOrderBffRsp]
part of 'orders.dart';

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezedJSON
abstract class OrdersBffReq with _$OrdersBffReq {
  const factory OrdersBffReq({required String accountId}) = _OrdersBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezedJSON
abstract class OrdersBffRsp with _$OrdersBffRsp {
  const factory OrdersBffRsp({required String title}) = _OrdersBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezedJSON
abstract class ConfirmOrderBffReq with _$ConfirmOrderBffReq {
  const factory ConfirmOrderBffReq({required String orderId}) = _ConfirmOrderBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezedJSON
abstract class ConfirmOrderBffRsp with _$ConfirmOrderBffRsp {
  const factory ConfirmOrderBffRsp({required String confirmationId}) = _ConfirmOrderBffRsp;
}
''');
      File(p.join(root.path, 'orders.v.dart')).writeAsStringSync(r'''
part of 'orders.dart';

@FrAcddPage(mode: FrAcddMode.bff, namespace: 'orders', version: 3)
class OrdersView {}
''');

      final schema = ContractExtractor().extractFromFile(shell.path);

      expect(schema.source, p.normalize(shell.path));
      expect(schema.namespace, 'orders');
      expect(schema.version, 3);
      expect(schema.figmaReference, 'https://www.figma.com/design/orders');
      expect(schema.routePath, '/orders');
      expect(schema.apis, hasLength(2));
      expect(schema.apis.first.requestRefs, ['OrdersBffReq']);
      expect(schema.apis.first.responseRefs, ['OrdersBffRsp']);
      expect(schema.apis.last.requestRefs, ['ConfirmOrderBffReq']);
      expect(schema.apis.last.responseRefs, ['ConfirmOrderBffRsp']);
      expect(
        schema.dtos.map((dto) => dto.name),
        orderedEquals([
          'OrdersBffReq',
          'OrdersBffRsp',
          'ConfirmOrderBffReq',
          'ConfirmOrderBffRsp',
        ]),
      );
    });

    test('supports named part-of declarations', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_named_part_');
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync("library orders;\npart 'orders.c.dart';\n");
      File(p.join(root.path, 'orders.c.dart')).writeAsStringSync(r'''
/// BFF-API: -
part of orders;

@FrAcddPage(mode: FrAcddMode.bff, namespace: 'orders')
class OrdersView {}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class OrdersDto with _$OrdersDto {
  const factory OrdersDto({required String title}) = _OrdersDto;
}
''');

      final schema = ContractExtractor().extractFromFile(shell.path);

      expect(schema.namespace, 'orders');
      expect(schema.apis, isEmpty);
    });

    test('ignores contract-like text inside Dart strings', () {
      const source = r"""
/// BFF-API: -
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'orders')
class OrdersView {
  static const example = r'''
/// BFF-API:
/// GET /forged
/// [ForgedReq], [ForgedRsp]
''';
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class OrdersDto with _$OrdersDto {
  const factory OrdersDto({required String title}) = _OrdersDto;
}
""";

      final schema = ContractExtractor().extractFromSource(
        source,
        sourcePath: 'orders.dart',
      );

      expect(schema.apis, isEmpty);
    });

    test('rejects duplicate part declarations', () {
      final root = Directory.systemTemp.createTempSync(
        'fr_acdd_duplicate_part_',
      );
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync("part 'orders.c.dart';\npart 'orders.c.dart';\n");
      File(
        p.join(root.path, 'orders.c.dart'),
      ).writeAsStringSync("part of 'orders.dart';\n");

      expect(
        () => ContractExtractor().extractFromFile(shell.path),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            contains('Duplicate Dart part'),
          ),
        ),
      );
    });

    test('rejects a missing authored part', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_missing_');
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync("part 'orders.c.dart';\n");

      expect(
        () => ContractExtractor().extractFromFile(shell.path),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            allOf(contains('Authored Dart part'), contains('does not exist')),
          ),
        ),
      );
    });

    test('rejects a part owned by another shell', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_wrong_owner_');
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync("part 'orders.c.dart';\n");
      File(
        p.join(root.path, 'orders.c.dart'),
      ).writeAsStringSync("part of 'other.dart';\n");

      expect(
        () => ContractExtractor().extractFromFile(shell.path),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            allOf(contains('belongs to'), contains('other.dart')),
          ),
        ),
      );
    });

    test('rejects an individual part as input', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_part_input_');
      addTearDown(() => root.deleteSync(recursive: true));
      final part = File(p.join(root.path, 'orders.c.dart'))
        ..writeAsStringSync("part of 'orders.dart';\n");

      expect(
        () => ContractExtractor().extractFromFile(part.path),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            allOf(contains('library shell'), contains('part of')),
          ),
        ),
      );
    });

    test('rejects duplicate canonical sections across authored parts', () {
      final root = Directory.systemTemp.createTempSync('fr_acdd_duplicate_');
      addTearDown(() => root.deleteSync(recursive: true));
      final shell = File(p.join(root.path, 'orders.dart'))
        ..writeAsStringSync("part 'orders.c.dart';\npart 'orders.v.dart';\n");
      File(p.join(root.path, 'orders.c.dart')).writeAsStringSync(r'''
/// BFF-API:
/// - GET /orders
///   [OrdersBffReq], [OrdersBffRsp]
part of 'orders.dart';

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class OrdersBffReq with _$OrdersBffReq {
  const factory OrdersBffReq() = _OrdersBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class OrdersBffRsp with _$OrdersBffRsp {
  const factory OrdersBffRsp({required String title}) = _OrdersBffRsp;
}
''');
      File(p.join(root.path, 'orders.v.dart')).writeAsStringSync(r'''
/// BFF-API:
/// - GET /orders/again
///   [OrdersBffReq], [OrdersBffRsp]
part of 'orders.dart';

@FrAcddPage(mode: FrAcddMode.bff, namespace: 'orders')
class OrdersView {}
''');

      expect(
        () => ContractExtractor().extractFromFile(shell.path),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            contains('at most one `BFF-API:` section'),
          ),
        ),
      );
    });

    test('rejects the removed BFF-UI-API label', () {
      const source = r'''
/// BFF-UI-API:
/// - GET /orders
///   [OrdersBffReq], [OrdersBffRsp]
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'orders')
class OrdersView {}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class OrdersBffReq with _$OrdersBffReq {
  const factory OrdersBffReq() = _OrdersBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class OrdersBffRsp with _$OrdersBffRsp {
  const factory OrdersBffRsp({required String title}) = _OrdersBffRsp;
}
''';

      expect(
        () => ContractExtractor().extractFromSource(
          source,
          sourcePath: 'orders.dart',
        ),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            allOf(contains('BFF-UI-API'), contains('BFF-API')),
          ),
        ),
      );
    });
  });
}
