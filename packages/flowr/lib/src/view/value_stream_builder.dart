part of './view.dart';

/// Signature for the `builder` function which takes the `BuildContext` and the current `value`
/// and is responsible for returning a widget which is to be rendered.
/// This is analogous to the `builder` function in [StreamBuilder].
typedef ValueStreamWidgetBuilder<M> =
    Widget Function(BuildContext context, M value, Widget? child);

/// Signature for the `buildWhen` function which takes the previous and
/// current `value` and is responsible for returning a [bool] which
/// determines whether to rebuild [ValueStreamBuilder] with the current `value`.
typedef ValueStreamBuilderCondition<M, T> =
    bool Function(T? preDistinct, T? curDistinct, M current);

/// {@template value_stream_builder}
/// [ValueStreamBuilder] handles building a widget in response to new `value`.
/// [ValueStreamBuilder] is analogous to [StreamBuilder] but has simplified API to
/// reduce the amount of boilerplate code needed as well as [ValueStream]-specific
/// performance improvements.
///
/// [ValueStreamBuilder] requires [stream.hasValue] to always be `true`,
/// and the [stream] does not emit any error events.
/// See [ValueStreamHasNoValueError] and [UnhandledStreamError]
/// for more information.
///
/// Please refer to [ValueStreamListener] if you want to "do" anything in response to
/// `value` changes such as navigation, showing a dialog, etc...
///
/// [ValueStreamBuilder] handles building a widget in response to new `value`.
/// [ValueStreamBuilder] is analogous to [StreamBuilder] but has simplified API to
/// reduce the amount of boilerplate code needed as well as [ValueStream]-specific
/// performance improvements.
///
/// **Example**
///
/// ```dart
/// ValueStreamBuilder<T>(
///   stream: valueStream,
///   builder: (context, value, child) {
///     // return widget here based on valueStream's value
///   },
///   child: const SizedBox(), // Optional child widget that remains stable
/// );
/// ```
/// {@endtemplate}
///
/// {@template value_stream_builder_build_when}
/// An optional [buildWhen] can be implemented for more granular control over
/// how often [ValueStreamBuilder] rebuilds.
///
/// - [buildWhen] should only be used for performance optimizations as it
/// provides no security about the value passed to the [builder] function.
/// - [buildWhen] will be invoked on each [stream] `value` change.
/// - [buildWhen] takes the previous `value` and current `value` and must
/// return a [bool] which determines whether or not the [builder] function will
/// be invoked.
/// - The previous `value` will be initialized to the `value` of the [stream] when
/// the [ValueStreamBuilder] is initialized.
///
/// [buildWhen] is optional and if omitted, it will default to `true`.
///
/// [child] is optional but is good practice to use if part of
/// the widget subtree does not depend on the value of the [stream].
///
/// **Example**
///
/// ```dart
/// ValueStreamBuilder<T>(
///   stream: valueStream,
///   buildWhen: (previous, current) {
///     // return true/false to determine whether or not
///     // to rebuild the widget with valueStream's value
///   },
///   builder: (context, value, child) {
///     // return widget here based on valueStream's value
///   },
///   child: const SizedBox(), // Optional child widget that remains stable
/// )
/// ```
/// {@endtemplate}
class ValueStreamBuilder<M, T> extends StatefulWidget {
  /// {@macro value_stream_builder}
  /// {@macro value_stream_builder_build_when}
  const ValueStreamBuilder({
    super.key,
    required this.stream,
    this.distinctBy,
    required this.builder,
    this.buildWhen,
    this.child,
    this.isReplayValueStream = true,
  });

  /// The [ValueStream] that the [ValueStreamBuilder] will interact with.
  final ValueStream<M> stream;

  final T? Function(M event)? distinctBy;

  /// The [builder] function which will be invoked on each widget build.
  /// The [builder] takes the `BuildContext` and current `value` and
  /// must return a widget.
  /// This is analogous to the [builder] function in [StreamBuilder].
  final ValueStreamWidgetBuilder<M> builder;

  /// Takes the previous `value` and the current `value` and is responsible for
  /// returning a [bool] which determines whether or not to trigger
  /// [builder] with the current `value`.
  final ValueStreamBuilderCondition<M, T>? buildWhen;

  /// A [ValueStream]-independent widget which is passed back to the [builder].
  ///
  /// This argument is optional and can be null if the entire widget subtree the
  /// [builder] builds depends on the value of the [stream]. For
  /// example, in the case where the [stream] is a [String] and the
  /// [builder] returns a [Text] widget with the current [String] value, there
  /// would be no useful [child].
  final Widget? child;

  /// Whether or not the [stream] emits the last value
  /// like [BehaviorSubject] does.
  ///
  /// Defaults to `true`.
  final bool isReplayValueStream;

  @override
  State<ValueStreamBuilder<M, T>> createState() =>
      _ValueStreamBuilderState<M, T>();

  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties
      ..add(DiagnosticsProperty<ValueStream<M>>('stream', stream))
      ..add(
        DiagnosticsProperty<bool>('isReplayValueStream', isReplayValueStream),
      )
      ..add(
        ObjectFlagProperty<ValueStreamBuilderCondition<M, T>?>.has(
          'buildWhen',
          buildWhen,
        ),
      )
      ..add(
        ObjectFlagProperty<ValueStreamWidgetBuilder<M>>.has('builder', builder),
      )
      ..add(ObjectFlagProperty<Widget?>.has('child', child));
  }
}

class _ValueStreamBuilderState<M, T> extends State<ValueStreamBuilder<M, T>> {
  late M _currentValue;

  @override
  void initState() {
    super.initState();
    _currentValue = widget.stream.value;
  }

  @override
  Widget build(BuildContext context) => ValueStreamListener<M, T>(
    stream: widget.stream,
    distinctBy: widget.distinctBy,
    isReplayValueStream: widget.isReplayValueStream,
    listener: (context, preDistinct, curDistinct, value) {
      if (widget.buildWhen?.call(preDistinct, curDistinct, value) ?? true) {
        setState(() => _currentValue = value);
      }
    },
    child: widget.builder(context, _currentValue, widget.child),
  );
}
