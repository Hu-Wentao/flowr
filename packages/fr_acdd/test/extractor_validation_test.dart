import 'package:fr_acdd/fr_acdd.dart';
import 'package:test/test.dart';

void main() {
  test('rejects DTOs without any supported Freezed annotation', () {
    final source = r'''
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:fr_acdd/fr_acdd.dart';

abstract class StatelessWidget {
  const StatelessWidget({this.key});
  final Object? key;
}

/// Route: AppRouter.invalid
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'invalid_page')
class InvalidPage extends StatelessWidget {
  const InvalidPage({super.key});
}

@FrAcddDto(kind: FrAcddDtoKind.root)
class InvalidRootModel with _$InvalidRootModel {
  const factory InvalidRootModel({
    @FrAcddField(tag: 1) required String title,
  }) = _InvalidRootModel;
}
''';

    expect(
      () => ContractExtractor().extractFromSource(
        source,
        sourcePath: 'memory.dart',
      ),
      throwsA(
        isA<StateError>().having(
          (error) => error.message,
          'message',
          contains('does not declare a supported Freezed annotation'),
        ),
      ),
    );
  });

  test('rejects multiple redirecting freezed factories for DTOs', () {
    final source = r'''
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:fr_acdd/fr_acdd.dart';

abstract class StatelessWidget {
  const StatelessWidget({this.key});
  final Object? key;
}

/// Route: AppRouter.invalid
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'invalid_page')
class InvalidPage extends StatelessWidget {
  const InvalidPage({super.key});
}

@FrAcddDto(kind: FrAcddDtoKind.root)
@Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
)
class InvalidRootModel with _$InvalidRootModel {
  const factory InvalidRootModel.loading() = _InvalidRootModelLoading;

  const factory InvalidRootModel.ready({
    @FrAcddField(tag: 1) required String title,
  }) = _InvalidRootModelReady;
}
''';

    expect(
      () => ContractExtractor().extractFromSource(
        source,
        sourcePath: 'memory.dart',
      ),
      throwsA(
        isA<StateError>().having(
          (error) => error.message,
          'message',
          contains('Freezed unions are not supported for @FrAcddDto'),
        ),
      ),
    );
  });
}
