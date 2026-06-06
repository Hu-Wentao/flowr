import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test(
    'extracts bffDto schemas and renders proto with route and figma comments',
    () {
      final fixturePath = p.join(
        Directory.current.path,
        'test',
        'fixtures',
        'notifications_page.dart',
      );

      final schema = ContractExtractor().extractFromFile(fixturePath);

      expect(schema.supported, isTrue);
      expect(schema.mode, FrAcddMode.bffDto);
      expect(schema.namespace, 'notifications_page');
      expect(schema.version, 2);
      expect(schema.routePath, 'AppRouter.notifications');
      expect(
        schema.figmaReference,
        'https://www.figma.com/file/abc123/notifications',
      );
      expect(schema.dtos, hasLength(3));
      expect(
        schema.dtos.map((dto) => dto.name),
        orderedEquals([
          'NotificationsScreenDataModel',
          'NotificationsTabDataModel',
          'NotificationsTabSummaryModel',
        ]),
      );
      expect(
        schema.dtos.map((dto) => dto.kind),
        isNot(contains(FrAcddDtoKind.state)),
      );

      final proto = const ProtoSchemaBuilder().build(schema);
      expect(proto, contains('syntax = "proto3";'));
      expect(proto, contains('package notifications_page.v2;'));
      expect(proto, contains('// Route: AppRouter.notifications'));
      expect(
        proto,
        contains('// Figma: https://www.figma.com/file/abc123/notifications'),
      );
      expect(proto, contains('import "google/protobuf/timestamp.proto";'));
      expect(proto, contains('message NotificationsScreenDataModel {'));
      expect(proto, contains('repeated NotificationsTabDataModel tabs = 1;'));
      expect(proto, contains('string selected_tab = 2;'));
      expect(proto, contains('google.protobuf.Timestamp updated_at = 3;'));
      expect(
        proto,
        contains(
          'map<string, NotificationsTabSummaryModel> counts_by_tab = 4;',
        ),
      );
      expect(proto, contains('optional string priority = 3;'));
    },
  );
}
