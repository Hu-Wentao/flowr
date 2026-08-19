import 'package:flowr/flowr_mvvm_support.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('exports FrReadContextX', (tester) async {
    late BuildContext context;

    await tester.pumpWidget(
      Provider<String>.value(
        value: 'FlowR',
        child: Builder(
          builder: (buildContext) {
            context = buildContext;
            return const SizedBox();
          },
        ),
      ),
    );

    expect(context.read<String>(), 'FlowR');
  });
}
