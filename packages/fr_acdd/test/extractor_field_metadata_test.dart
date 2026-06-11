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
    expect(tabs.nestedRef, 'NotificationsTabDataModel');
    expect(tabs.nullable, isFalse);
    expect(tabs.repeated, isTrue);
    expect(tabs.defaultCode, '<NotificationsTabDataModel>[]');

    expect(updatedAt.tag, 2);
    expect(updatedAt.nullable, isTrue);
    expect(updatedAt.normalizedType, 'datetime');

    expect(countsByTab.wireName, 'counts_by_tab');
    expect(countsByTab.tag, 3);
    expect(countsByTab.dartType, 'Map<String, NotificationsTabSummaryModel>');
    expect(
      countsByTab.normalizedType,
      'map<string, NotificationsTabSummaryModel>',
    );
  });
}
