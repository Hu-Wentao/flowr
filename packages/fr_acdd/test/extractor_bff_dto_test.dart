import 'dart:io';

import 'package:fr_acdd/fr_acdd.dart';
import 'package:path/path.dart' as p;
import 'package:test/test.dart';

void main() {
  test(
    'extracts bff schemas and renders proto with route and figma comments',
    () {
      final fixturePath = p.join(
        Directory.current.path,
        'test',
        'fixtures',
        'notifications_page.dart',
      );

      final schema = ContractExtractor().extractFromFile(fixturePath);

      expect(schema.supported, isTrue);
      expect(schema.mode, FrAcddMode.bff);
      expect(schema.namespace, 'notifications_page');
      expect(schema.version, 2);
      expect(schema.routePath, 'AppRouter.notifications');
      expect(
        schema.figmaReference,
        'https://www.figma.com/file/abc123/notifications',
      );
      expect(
        schema.apis.map((api) => api.suggestedPath),
        orderedEquals([
          '<BASE>/notifications-page/bootstrap',
          '<BASE>/notifications-page/tabs',
          '<BASE>/notifications-page/counts-by-tab',
        ]),
      );
      expect(
        schema.apis.map((api) => api.method),
        orderedEquals(['GET', 'GET', 'GET']),
      );
      expect(
        schema.apis.map((api) => api.requestRefs.join(',')).toList(),
        orderedEquals([
          'NotificationsBootstrapReq',
          'NotificationsTabsReq',
          'NotificationsCountsByTabReq',
        ]),
      );
      expect(
        schema.apis.map((api) => api.responseRefs.join(',')).toList(),
        orderedEquals([
          'NotificationsScreenDataModel',
          'NotificationsTabDataModel',
          'NotificationsTabSummaryModel',
        ]),
      );
      expect(schema.dtos, hasLength(6));
      expect(
        schema.dtos.map((dto) => dto.name),
        orderedEquals([
          'NotificationsBootstrapReq',
          'NotificationsTabsReq',
          'NotificationsCountsByTabReq',
          'NotificationsScreenDataModel',
          'NotificationsTabDataModel',
          'NotificationsTabSummaryModel',
        ]),
      );

      final proto = const ProtoSchemaBuilder().build(schema);
      expect(proto, contains('syntax = "proto3";'));
      expect(proto, contains('package notifications_page.v2;'));
      expect(proto, contains('// Route: AppRouter.notifications'));
      expect(
        proto,
        contains('// Figma: https://www.figma.com/file/abc123/notifications'),
      );
      expect(proto, contains('// BFF-API:'));
      expect(proto, contains('// - GET <BASE>/notifications-page/bootstrap'));
      expect(
        proto,
        contains(
          '//   [NotificationsBootstrapReq], [NotificationsScreenDataModel]',
        ),
      );
      expect(proto, contains('import "google/protobuf/timestamp.proto";'));
      expect(proto, contains('message NotificationsBootstrapReq {'));
      expect(proto, contains('message NotificationsScreenDataModel {'));
      expect(proto, contains('repeated NotificationsTabDataModel tabs = 1;'));
      expect(proto, contains('google.protobuf.Timestamp updatedAt = 2;'));
      expect(
        proto,
        contains('map<string, NotificationsTabSummaryModel> countsByTab = 3;'),
      );
      expect(proto, contains('optional string priority = 3;'));
    },
  );

  test('rejects unsupported dto kinds', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

/// Route: AppRouter.invalid
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'invalid_page',
)
class InvalidPage {}

@FrAcddDto(kind: FrAcddDtoKind.state)
@FrAcddFreezed
class InvalidPayload with _$InvalidPayload {
  const factory InvalidPayload({
    @FrAcddField(tag: 1) required String title,
  }) = _InvalidPayload;
}
''';

    expect(
      () => ContractExtractor().extractFromSource(
        source,
        sourcePath: 'test/fixtures/invalid_page.dart',
      ),
      throwsA(
        isA<StateError>().having(
          (error) => error.message,
          'message',
          contains('Unsupported FrAcddDto.kind'),
        ),
      ),
    );
  });

  test('rejects legacy @freezed annotations', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';

/// Route: AppRouter.legacy
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'legacy_page',
)
class LegacyPage {}

@FrAcddDto(kind: FrAcddDtoKind.root)
@freezed
class LegacyRoot with _$LegacyRoot {
  const factory LegacyRoot({
    @FrAcddField(tag: 1) required String title,
  }) = _LegacyRoot;
}
''';

    expect(
      () => ContractExtractor().extractFromSource(
        source,
        sourcePath: 'test/fixtures/legacy_page.dart',
      ),
      throwsA(
        isA<StateError>().having(
          (error) => error.message,
          'message',
          contains('Use `@FrAcddFreezed` or `@Freezed(...)`'),
        ),
      ),
    );
  });

  test('infers multiple api branches when API comments are missing', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';

/// Route: AppRouter.dashboard
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'dashboard_page',
)
class DashboardPage {}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class DashboardPayloadModel with _$DashboardPayloadModel {
  const factory DashboardPayloadModel({
    @FrAcddField(tag: 1) required String title,
    @FrAcddField(tag: 2, nestedRef: DashboardCardModel)
    required List<DashboardCardModel> cards,
    @FrAcddField(tag: 3)
    required Map<String, DashboardMetricModel> metrics,
  }) = _DashboardPayloadModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class DashboardCardModel with _$DashboardCardModel {
  const factory DashboardCardModel({
    @FrAcddField(tag: 1) required String id,
  }) = _DashboardCardModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class DashboardMetricModel with _$DashboardMetricModel {
  const factory DashboardMetricModel({
    @FrAcddField(tag: 1) required int total,
  }) = _DashboardMetricModel;
}
''';

    final schema = ContractExtractor().extractFromSource(
      source,
      sourcePath: 'test/fixtures/dashboard_page.dart',
    );

    expect(
      schema.apis.map((api) => api.suggestedPath),
      orderedEquals([
        '<BASE>/dashboard-page/bootstrap',
        '<BASE>/dashboard-page/cards',
        '<BASE>/dashboard-page/metrics',
      ]),
    );
  });
}
