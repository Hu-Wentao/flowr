import 'package:flowr/src/error.dart';
import 'package:flowr/src/view/value_stream_widget.dart';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('ValueStreamBuilder reports missing initial value', (
    tester,
  ) async {
    final flutterErrors = <FlutterErrorDetails>[];
    final oldOnError = FlutterError.onError;
    FlutterError.onError = flutterErrors.add;
    addTearDown(() => FlutterError.onError = oldOnError);

    final subject = ValueStreamController<int>();
    addTearDown(subject.close);

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: ValueStreamBuilder<int>(
          stream: subject.stream,
          builder: (_, value, __) => Text('$value'),
        ),
      ),
    );

    expect(find.byType(ErrorWidget), findsOneWidget);
    expect(
      flutterErrors.single.exception,
      isA<ValueStreamHasNoValueError<int>>(),
    );
  });

  testWidgets('ValueStreamConsumer reports initial stream errors', (
    tester,
  ) async {
    final flutterErrors = <FlutterErrorDetails>[];
    final oldOnError = FlutterError.onError;
    FlutterError.onError = flutterErrors.add;
    addTearDown(() => FlutterError.onError = oldOnError);

    final subject = ValueStreamController<int>.seeded(1)..addError('boom');
    addTearDown(subject.close);

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: ValueStreamConsumer<int>(
          stream: subject.stream,
          listener: (_, __, ___) {},
          builder: (_, value, __) => Text('$value'),
        ),
      ),
    );

    expect(find.byType(ErrorWidget), findsOneWidget);
    expect(flutterErrors.single.exception, isA<UnhandledStreamError>());
  });

  testWidgets('ValueStreamListener reports initial stream errors', (
    tester,
  ) async {
    final flutterErrors = <FlutterErrorDetails>[];
    final oldOnError = FlutterError.onError;
    FlutterError.onError = flutterErrors.add;
    addTearDown(() => FlutterError.onError = oldOnError);

    final subject = ValueStreamController<int>.seeded(1)
      ..addError('later boom');
    addTearDown(subject.close);

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: ValueStreamListener<int>(
          stream: subject.stream,
          listener: (_, __, ___) {},
          child: const Text('child'),
        ),
      ),
    );

    expect(find.byType(ErrorWidget), findsOneWidget);
    expect(flutterErrors.single.exception, isA<UnhandledStreamError>());
  });
}
