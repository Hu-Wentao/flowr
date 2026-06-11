import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test(
    'renders JSON5 with figma comments, api paths, and nested DTO comments',
    () {
      final fixturePath = p.join(
        Directory.current.path,
        'test',
        'fixtures',
        'notifications_page.dart',
      );

      final schema = ContractExtractor().extractFromFile(fixturePath);
      final json5 = const Json5SchemaBuilder().build(schema);

      expect(
        json5,
        contains('// Figma: https://www.figma.com/file/abc123/notifications'),
      );
      expect(json5, contains('// Suggested API paths:'));
      expect(
        json5,
        contains(
          '// - /bff/notifications/tabs: GET /bff/notifications/tabs owns tabs shell and tab-level payload loading.',
        ),
      );
      expect(json5, contains('// JSON5 payload shape:'));
      expect(json5, contains('// Dart type: List<NotificationsTabDataModel>'));
      expect(json5, contains('// Nested DTO: NotificationsTabDataModel'));
      expect(json5, contains('tabs: ['));
      expect(json5, contains("updated_at: '2026-01-01T00:00:00Z'"));
      expect(json5, contains('counts_by_tab: {'));
    },
  );
}
