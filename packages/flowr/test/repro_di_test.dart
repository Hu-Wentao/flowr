import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class FooVM extends FrViewModel<String> {
  FooVM() : super('foo');
}

void main() {
  testWidgets('FrProvider.di should pull from GetIt by default', (
    tester,
  ) async {
    final getIt = GetIt.I;
    getIt.registerLazySingleton<FooVM>(() => FooVM());

    await tester.pumpWidget(
      MultiProvider(providers: [FrProvider<FooVM>.di()], child: Container()),
    );

    final context = tester.element(find.byType(Container));

    // This should not throw if FrProvider.di worked correctly
    final vm = Provider.of<FooVM>(context, listen: false);
    expect(vm, isA<FooVM>());
    expect(vm.value, 'foo');

    getIt.reset();
  });
}
