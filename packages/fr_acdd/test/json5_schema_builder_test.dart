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
      expect(json5, contains('- Request DTOs: [NotificationsTabsReq]'));
      expect(json5, contains('- Response DTOs: [NotificationsTabDataModel]'));
      expect(json5, contains('#### Request JSON5'));
      expect(json5, contains('#### Response JSON5'));
      expect(json5, contains('```json5'));
      expect(json5, contains('// Dart type: List<NotificationsTabDataModel>'));
      expect(json5, contains('// Nested DTO: NotificationsTabDataModel'));
      expect(json5, contains("tabId: 'string'"));
      expect(json5, contains("updatedAt: '2026-01-01T00:00:00Z'"));
      expect(json5, contains('countsByTab: {'));
    },
  );
}
