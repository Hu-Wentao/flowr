import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test(
    'renders markdown json5 contract with figma metadata and api request/response snippets',
    () {
      final fixturePath = p.join(
        Directory.current.path,
        'test',
        'fixtures',
        'notifications_page.dart',
      );

      final schema = ContractExtractor().extractFromFile(fixturePath);
      final json5 = const Json5SchemaBuilder().build(schema);

      expect(json5, contains('# Derived JSON5 Contract'));
      expect(
        json5,
        contains('- Figma: `https://www.figma.com/file/abc123/notifications`'),
      );
      expect(json5, contains('## BFF-API'));
      expect(json5, contains('### GET <BASE>/notifications-page/tabs'));
      expect(json5, contains('- Request DTOs: [NotificationsTabsBffReq]'));
      expect(json5, contains('- Response DTOs: [NotificationsTabsBffRsp]'));
      expect(json5, contains('#### Request JSON5'));
      expect(json5, contains('#### Response JSON5'));
      expect(json5, contains('```json5'));
      expect(json5, contains('// Dart type: List<NotificationsTabDto>'));
      expect(json5, contains('// Nested DTO: NotificationsTabDto'));
      expect(json5, contains("tabId: 'string'"));
      expect(json5, contains("updatedAt: '2026-01-01T00:00:00Z'"));
      expect(json5, contains('countsByTab: {'));
    },
  );

  test('json export can omit tags and bare field annotations', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';

/// BFF-API:
/// - GET <BASE>/untagged-page/bootstrap
///   [UntaggedBffReq], [UntaggedBffRsp]
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'untagged_page')
class UntaggedPage {}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class UntaggedBffReq with _$UntaggedBffReq {
  const factory UntaggedBffReq({
    String? query,
  }) = _UntaggedBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class UntaggedBffRsp with _$UntaggedBffRsp {
  const factory UntaggedBffRsp({
    required String title,
    @FrAcddField() int? count,
    @FrAcddField(include: false) String? debugOnly,
  }) = _UntaggedBffRsp;
}
''';

    final schema = ContractExtractor().extractFromSource(
      source,
      sourcePath: 'test/fixtures/untagged_page.dart',
    );
    final rootDto = schema.dtos.firstWhere(
      (dto) => dto.name == 'UntaggedBffRsp',
    );

    expect(
      rootDto.fields.map((field) => field.name),
      orderedEquals(['title', 'count']),
    );
    expect(rootDto.fields.every((field) => field.tag == null), isTrue);

    final json5 = const Json5SchemaBuilder().build(schema);
    expect(json5, contains('### GET <BASE>/untagged-page/bootstrap'));
    expect(json5, contains("title: 'string'"));
    expect(json5, contains('count: 0'));
    expect(json5, isNot(contains('debugOnly')));
  });
}
