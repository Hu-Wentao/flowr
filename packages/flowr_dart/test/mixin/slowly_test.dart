import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class SlowlyVM extends FlowR<int> with TestLoggableMx {
  @override
  int get initValue => 0;

  Future<void> addWithMutex(int v) async {
    await update((o) async {
      await Future.delayed(Duration(milliseconds: 100));
      return o + v;
    }, mutexTag: 'add');
  }

  void addWithDebounce(int v) {
    update((o) => o + v, debounceTag: 'add', slowlyMs: 50);
  }

  void addWithThrottle(int v) {
    update((o) => o + v, throttleTag: 'add', slowlyMs: 50);
  }
}

void main() {
  group('SlowlyMx', () {
    test('mutex (exhaust)', () async {
      final vm = SlowlyVM();
      // first call starts and takes 100ms
      final f1 = vm.addWithMutex(1);
      // second call should be ignored because 'add' is locked
      final f2 = vm.addWithMutex(2);

      await Future.wait([f1, f2]);
      expect(vm.value, 1);

      // now it should work again
      await vm.addWithMutex(3);
      expect(vm.value, 4);
    });

    test('debounce', () async {
      final vm = SlowlyVM();
      vm.addWithDebounce(1);
      vm.addWithDebounce(2);
      vm.addWithDebounce(3);

      await Future.delayed(Duration(milliseconds: 100));
      expect(vm.value, 3);
    });

    test('throttle', () async {
      final vm = SlowlyVM();
      vm.addWithThrottle(1); // runs
      vm.addWithThrottle(2); // ignored
      vm.addWithThrottle(3); // ignored

      await Future.delayed(Duration(milliseconds: 20));
      expect(vm.value, 1);

      await Future.delayed(Duration(milliseconds: 40));
      vm.addWithThrottle(4); // runs (after 50ms)
      expect(vm.value, 5);
    });
  });
}
