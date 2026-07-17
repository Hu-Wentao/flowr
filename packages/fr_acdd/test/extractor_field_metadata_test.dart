import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test('extracts field metadata used for protobuf generation', () {
    final fixturePath = p.join(
      Directory.current.path,
      'test',
      'fixtures',
      'notifications_page.dart',
    );

    final schema = ContractExtractor().extractFromFile(fixturePath);
    final rootDto = schema.dtos.firstWhere(
      (dto) => dto.kind == FrAcddDtoKind.root,
    );
    final tabs = rootDto.fields.firstWhere((field) => field.name == 'tabs');
    final updatedAt = rootDto.fields.firstWhere(
      (field) => field.name == 'updatedAt',
    );
    final countsByTab = rootDto.fields.firstWhere(
      (field) => field.name == 'countsByTab',
    );

    expect(tabs.wireName, 'tabs');
    expect(tabs.tag, 1);
    expect(tabs.nestedRef, 'NotificationsTabDto');
    expect(tabs.nullable, isFalse);
    expect(tabs.repeated, isTrue);
    expect(tabs.defaultCode, '<NotificationsTabDto>[]');

    expect(updatedAt.tag, 2);
    expect(updatedAt.nullable, isTrue);
    expect(updatedAt.normalizedType, 'datetime');

    expect(countsByTab.wireName, 'countsByTab');
    expect(countsByTab.tag, 3);
    expect(countsByTab.dartType, 'Map<String, NotificationsTabSummaryDto>?');
    expect(countsByTab.normalizedType, 'map');
    expect(countsByTab.mapKeyNormalizedType, 'string');
    expect(countsByTab.mapValueNormalizedType, 'object');
    expect(countsByTab.nestedRef, 'NotificationsTabSummaryDto');
  });
}
