import 'dart:async';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class TestDispose with DisposeMx {
  bool disposed = false;
  @override
  void dispose() {
    disposed = true;
  }
}

class TestAutoDispose extends TestDispose with SubsAutoDisposeMx<void> {
  T testAutoDispose<T extends StreamSubscription?>(T subs, {String? tag}) {
    return autoDispose<T>(subs, tag: tag);
  }
}

void main() {
  group('SubsAutoDisposeMx', () {
    test('autoDispose cancels subscriptions on dispose', () async {
      bool canceled = false;
      final controller = StreamController<int>(onCancel: () {
        canceled = true;
      });
      final tester = TestAutoDispose();
      final sub = controller.stream.listen((_) {});

      tester.testAutoDispose(sub, tag: 'sub1');
      expect(tester.subBy('sub1'), sub);

      tester.dispose();

      expect(canceled, true);
    });

    test('manual cancellation verification', () async {
      int cancelCount = 0;
      final controller = StreamController<int>(
        onCancel: () {
          cancelCount++;
        },
      );

      final sub = controller.stream.listen((event) {});
      final tester = TestAutoDispose();
      tester.testAutoDispose(sub);

      expect(cancelCount, 0);
      tester.dispose();
      expect(cancelCount, 1);
    });

    test('subBy returns the correct subscription', () {
      final tester = TestAutoDispose();
      final sub1 = Stream.empty().listen(null);
      final sub2 = Stream.empty().listen(null);

      tester.testAutoDispose(sub1, tag: 'one');
      tester.testAutoDispose(sub2, tag: 'two');

      expect(tester.subBy('one'), sub1);
      expect(tester.subBy('two'), sub2);

      tester.dispose();
    });
  });
}
