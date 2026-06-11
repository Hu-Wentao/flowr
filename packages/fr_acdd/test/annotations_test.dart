import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:fr_acdd/fr_acdd.dart';
import 'package:test/test.dart';

void main() {
  test('annotation types can be instantiated', () {
    const page = FrAcddPage(
      mode: FrAcddMode.bff,
      namespace: 'notifications_page',
      version: 2,
    );
    const dto = FrAcddDto(
      kind: FrAcddDtoKind.root,
      name: 'NotificationsScreenDataModel',
      description: 'Root notification payload.',
    );
    const field = FrAcddField(
      wireName: 'selected_tab',
      tag: 2,
      nestedRef: String,
      include: false,
    );

    expect(page.mode, FrAcddMode.bff);
    expect(page.namespace, 'notifications_page');
    expect(page.version, 2);
    expect(dto.kind, FrAcddDtoKind.root);
    expect(dto.name, 'NotificationsScreenDataModel');
    expect(dto.description, 'Root notification payload.');
    expect(field.wireName, 'selected_tab');
    expect(field.tag, 2);
    expect(field.nestedRef, String);
    expect(field.include, isFalse);
  });

  test('FrAcddFreezed exposes the dto preset', () {
    expect(FrAcddFreezed, isA<Freezed>());
    expect(FrAcddFreezed.copyWith, isTrue);
    expect(FrAcddFreezed.equal, isTrue);
    expect(FrAcddFreezed.toStringOverride, isTrue);
    expect(FrAcddFreezed.fromJson, isFalse);
    expect(FrAcddFreezed.toJson, isFalse);
  });

  test('enum values stay complete', () {
    expect(FrAcddMode.values, orderedEquals([FrAcddMode.api, FrAcddMode.bff]));
    expect(
      FrAcddDtoKind.values,
      orderedEquals([FrAcddDtoKind.root, FrAcddDtoKind.nested]),
    );
  });
}
