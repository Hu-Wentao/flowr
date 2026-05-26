import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class StmTest extends FlowR<int> {
  final events = <int>[];

  StmTest({required int initialState}) : super(initialState) {
    autoDispose(
      stream
          .distinctBy((e) => e)
          .switchMap((e) {
            return e % 2 != 0
                ? Stream.empty() // empty will not trigger onData
                : Stream.periodic(Duration(milliseconds: 10), (_) => e);
          })
          .listen(onData),
    );
  }

  void onData(event) {
    events.add(event);
  }
}

void main() {
  test('switchMap', () async {
    final vm = StmTest(initialState: 1);
    await vm.update((o) => 66);
    await Future.delayed(Duration(milliseconds: 25));
    expect(vm.events, isNotEmpty);
    expect(vm.events, everyElement(66));

    await vm.update((o) => 1);
    final count = vm.events.length;
    await Future.delayed(Duration(milliseconds: 25));
    expect(vm.value, 1);
    expect(vm.events.length, count);
    vm.dispose();
  });
}
