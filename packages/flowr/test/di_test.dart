import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class CountM {
  int v = 0;
  @override
  String toString() => "CountM {$v}";
}

class CountVM extends FrViewModel<CountM> {
  final String debugLabel;

  CountVM({this.debugLabel = ''});

  @override
  CountM get initValue => CountM();

  change(int v) => update((o) => o..v = v);
}

main() {
  group('di', () {
    test('lazy singleton', () {
      final sl = GetIt.asNewInstance();

      sl.registerLazySingleton<CountVM>(() => CountVM(debugLabel: 'vm1'));
      expect(sl<CountVM>().value.v, 0);
      expect(sl<CountVM>().debugLabel, 'vm1');

      sl<CountVM>().change(2);
      expect(sl<CountVM>().value.v, 2);
      expect(sl<CountVM>().debugLabel, 'vm1');

      /// dispose
      sl<CountVM>().dispose();
      expect(() => sl<CountVM>().change(3), throwsA(isA<StateError>()));

      /// re register
      sl.resetLazySingleton<CountVM>();

      sl<CountVM>().change(4);
      expect(sl<CountVM>().value.v, 4);
      expect(sl<CountVM>().debugLabel, 'vm1');
    });

    test('singleton', () {
      final sl = GetIt.asNewInstance();

      sl.registerSingleton<CountVM>(CountVM(debugLabel: 'vm1'));
      expect(sl<CountVM>().value.v, 0);
      expect(sl<CountVM>().debugLabel, 'vm1');

      sl<CountVM>().change(2);
      expect(sl<CountVM>().value.v, 2);
      expect(sl<CountVM>().debugLabel, 'vm1');

      /// dispose
      sl<CountVM>().dispose();
      expect(() => sl<CountVM>().change(3), throwsA(isA<StateError>()));

      /// re register
      sl.unregister<CountVM>();
      sl.registerSingleton<CountVM>(CountVM(debugLabel: 'vm2'));

      sl<CountVM>().change(4);
      expect(sl<CountVM>().value.v, 4);
      expect(sl<CountVM>().debugLabel, 'vm2');
    });
  });
}
