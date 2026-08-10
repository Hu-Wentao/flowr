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
          'NotificationsBootstrapBffReq',
          'NotificationsTabsBffReq',
          'NotificationsCountsByTabBffReq',
        ]),
      );
      expect(
        schema.apis.map((api) => api.responseRefs.join(',')).toList(),
        orderedEquals([
          'NotificationsBootstrapBffRsp',
          'NotificationsTabsBffRsp',
          'NotificationsCountsByTabBffRsp',
        ]),
      );
      expect(schema.dtos, hasLength(8));
      expect(
        schema.dtos.map((dto) => dto.name),
        orderedEquals([
          'NotificationsBootstrapBffReq',
          'NotificationsTabsBffReq',
          'NotificationsCountsByTabBffReq',
          'NotificationsBootstrapBffRsp',
          'NotificationsTabsBffRsp',
          'NotificationsCountsByTabBffRsp',
          'NotificationsTabDto',
          'NotificationsTabSummaryDto',
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
      expect(proto, contains('// BFF-UI-API:'));
      expect(proto, contains('// - GET <BASE>/notifications-page/bootstrap'));
      expect(
        proto,
        contains(
          '//   [NotificationsBootstrapBffReq], [NotificationsBootstrapBffRsp]',
        ),
      );
      expect(proto, contains('import "google/protobuf/timestamp.proto";'));
      expect(proto, contains('message NotificationsBootstrapBffReq {'));
      expect(proto, contains('message NotificationsBootstrapBffRsp {'));
      expect(proto, contains('repeated NotificationsTabDto tabs = 1;'));
      expect(proto, contains('google.protobuf.Timestamp updatedAt = 2;'));
      expect(
        proto,
        contains('map<string, NotificationsTabSummaryDto> countsByTab = 3;'),
      );
      expect(proto, contains('optional string priority = 3;'));
    },
  );

  test('rejects nonstandard BFF boundary and internal DTO suffixes', () {
    final fixturePath = p.join(
      Directory.current.path,
      'test',
      'fixtures',
      'notifications_page.dart',
    );
    final source = File(fixturePath).readAsStringSync();
    final cases = <String, String>{
      'NotificationsBootstrapBffReq': 'NotificationsBootstrapReq',
      'NotificationsBootstrapBffRsp': 'NotificationsBootstrapResponse',
      'NotificationsTabDto': 'NotificationsTabData',
    };

    for (final entry in cases.entries) {
      expect(
        () => ContractExtractor().extractFromSource(
          source.replaceAll(entry.key, entry.value),
          sourcePath: 'test/fixtures/invalid_naming.dart',
        ),
        throwsA(isA<StateError>()),
        reason: '${entry.value} must be rejected',
      );
    }
  });

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
          contains(
            'Use `@FrAcddFreezed`, `@FrAcddFreezedJSON`, or `@Freezed(...)`',
          ),
        ),
      ),
    );
  });

  test('accepts FrAcddFreezedJSON annotations for extractable dto classes', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';

/// Route: AppRouter.json
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'json_page',
)
class JsonPage {}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezedJSON
class JsonBffRsp with _$JsonBffRsp {
  const factory JsonBffRsp({
    required String title,
  }) = _JsonBffRsp;
}
''';

    final schema = ContractExtractor().extractFromSource(
      source,
      sourcePath: 'test/fixtures/json_page.dart',
    );

    expect(schema.dtos, hasLength(1));
    expect(schema.dtos.single.name, 'JsonBffRsp');
    expect(schema.dtos.single.kind, FrAcddDtoKind.root);
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
class DashboardBffRsp with _$DashboardBffRsp {
  const factory DashboardBffRsp({
    @FrAcddField(tag: 1) required String title,
    @FrAcddField(tag: 2, nestedRef: DashboardCardBffRsp)
    required List<DashboardCardBffRsp> cards,
    @FrAcddField(tag: 3)
    required Map<String, DashboardMetricBffRsp> metrics,
  }) = _DashboardBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class DashboardCardBffRsp with _$DashboardCardBffRsp {
  const factory DashboardCardBffRsp({
    @FrAcddField(tag: 1) required String id,
  }) = _DashboardCardBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class DashboardMetricBffRsp with _$DashboardMetricBffRsp {
  const factory DashboardMetricBffRsp({
    @FrAcddField(tag: 1) required int total,
  }) = _DashboardMetricBffRsp;
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

  test('derives nested child page base paths from the page folder chain', () {
    const source = r'''
import 'package:fr_acdd/fr_acdd.dart';

/// Route: AppRouter.subPage
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'sub_page',
)
class SubPage {}

@FrAcddDto(kind: FrAcddDtoKind.root)
@FrAcddFreezed
class SubPageDto with _$SubPageDto {
  const factory SubPageDto({
    required SubPageSummaryBffRsp summary,
  }) = _SubPageDto;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class SubPageSummaryBffRsp with _$SubPageSummaryBffRsp {
  const factory SubPageSummaryBffRsp({
    required String title,
  }) = _SubPageSummaryBffRsp;
}
''';

    final schema = ContractExtractor().extractFromSource(
      source,
      sourcePath: 'lib/page/home_page/sub_page/sub_page.dart',
    );

    expect(
      schema.apis.map((api) => api.suggestedPath),
      orderedEquals(['<BASE>/home-page/sub-page/summary']),
    );
  });
}
