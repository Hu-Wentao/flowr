import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test('marks api mode pages as unsupported for BFF DTO export', () {
    final fixturePath = p.join(
      Directory.current.path,
      'test',
      'fixtures',
      'account_details_page.dart',
    );

    final schema = ContractExtractor().extractFromFile(fixturePath);

    expect(schema.supported, isFalse);
    expect(schema.mode, FrAcddMode.api);
    expect(schema.namespace, 'account_details_page');
    expect(schema.routePath, 'AppRouter.accountDetails');
    expect(schema.figmaReference, isNull);
    expect(schema.reason, 'page uses api mode; bff dto export disabled');
    expect(
      () => const ProtoSchemaBuilder().build(schema),
      throwsA(isA<StateError>()),
    );
    expect(
      () => const Json5SchemaBuilder().build(schema),
      throwsA(isA<StateError>()),
    );
  });
}
