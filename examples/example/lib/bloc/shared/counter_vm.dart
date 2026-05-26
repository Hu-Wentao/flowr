import 'package:flowr/flowr_mvvm.dart';

/// A shared Model used across all bloc-based examples.
class CounterModel {
  final int count;
  final String label;

  const CounterModel({this.count = 0, this.label = 'Counter'});

  CounterModel copyWith({int? count, String? label}) => CounterModel(
        count: count ?? this.count,
        label: label ?? this.label,
      );

  @override
  String toString() => 'CounterModel(count: $count, label: $label)';
}

/// A shared ViewModel used across all bloc-based examples.
///
/// [FrViewModel] extends [FlowR<CounterModel>] which implements
/// [StateStreamable<CounterModel>], so it can be passed directly
/// to the `bloc` parameter of [ValueStreamBuilder], [ValueStreamConsumer],
/// and [ValueStreamListener].
class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel({CounterModel initialState = const CounterModel()})
      : super(initialState);

  /// Increment counter by [amount].
  void increment({int amount = 1}) => update((old) {
        logger('increment: $amount');
        return old.copyWith(count: old.count + amount);
      });

  /// Set a new label.
  void updateLabel(String newLabel) => update((old) {
        logger('updateLabel: $newLabel');
        return old.copyWith(label: newLabel);
      });
}
