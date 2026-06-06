import 'package:fr_acdd/fr_acdd.dart';
import 'package:test/test.dart';

void main() {
  test('annotation types can be instantiated', () {
    const page = FrAcddPage(
      mode: FrAcddMode.bffDto,
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

    expect(page.mode, FrAcddMode.bffDto);
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

  test('enum values stay complete', () {
    expect(
      FrAcddMode.values,
      orderedEquals([FrAcddMode.api, FrAcddMode.bffDto]),
    );
    expect(
      FrAcddDtoKind.values,
      orderedEquals([
        FrAcddDtoKind.root,
        FrAcddDtoKind.nested,
        FrAcddDtoKind.state,
        FrAcddDtoKind.ignored,
      ]),
    );
  });
}
