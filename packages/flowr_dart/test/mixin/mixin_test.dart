import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<String> {
  Foo({required String initialState}) : super(initialState);

  Future<void> appendWith(String n) async {
    logger('append $n');
    await update((old) => '$old$n');
  }

  updateValueSkpNull(String? v) => update((o) => skpNull(v, 'v==1, skip'));

  updateValueSkipIf0(String v) => update((o) {
    skpIf(v == '0', 'v==0, skip');
    return v;
  });
}

class TestService extends IService {
  bool disposed = false;
  @override
  void dispose() {
    disposed = true;
    super.dispose();
  }
}

void main() {
  test('IService and DisposeMx', () {
    final service = TestService();
    expect(service.disposed, false);
    service.dispose();
    expect(service.disposed, true);
  });

  test('logger (appendWith)', () async {
    final foo = Foo(initialState: 'hello');
    await foo.appendWith(' world');
    expect(foo.value, 'hello world');
  });

  group('RunCatchingMx', () {
    test('skip', () {
      final foo = Foo(initialState: 'hello');

      foo.updateValueSkpNull('world');
      expect(foo.value, 'world');
      foo.updateValueSkpNull(null);
      expect(foo.value, 'world');
    });
    test('skipIf', () {
      final foo = Foo(initialState: 'hello');

      foo.updateValueSkipIf0('world');
      expect(foo.value, 'world');
      foo.updateValueSkipIf0('0');
      expect(foo.value, 'world');
    });
  });
}
