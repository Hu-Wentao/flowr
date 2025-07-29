part of './view.dart';

/// below code is from rxdart_flutter package; but support rxdart 0.27.0+

/// Signature for the `listener` function which takes the `BuildContext` along
/// with the previous and current `value` and is responsible for
/// executing in response to `value` changes.
typedef ValueStreamWidgetListener<M, T> = void Function(
  BuildContext context,
  T? preDistinct,
  T? curDistinct,
  M value,
);

/// {@template value_stream_listener}
/// Takes a [ValueStreamWidgetListener] and a [stream] and invokes
/// the [listener] in response to `value` changes in the [stream].
///
/// It should be used for functionality that needs to occur only in response to
/// a `value` change such as navigation, showing a `SnackBar`, showing
/// a `Dialog`, etc...
///
/// The [listener] is guaranteed to only be called once for each `value` change
/// unlike the `builder` in `ValueStreamBuilder`.
///
/// [ValueStreamListener] requires [stream.hasValue] to always be `true`,
/// and the [stream] does not emit any error events.
/// See [ValueStreamHasNoValueError] and [UnhandledStreamError]
/// for more information.
///
/// **Example**
///
/// ```dart
/// ValueStreamListener<T>(
///   stream: valueStream,
///   listener: (context, previous, current) {
///     // do stuff here based on valueStream's
///     // previous and current values
///   },
///   child: Container(),
/// )
/// ```
/// {@endtemplate}
class ValueStreamListener<M, T> extends StatefulWidget {
  /// {@macro value_stream_listener}
  const ValueStreamListener({
    super.key,
    required this.stream,
    this.distinctBy,
    required this.listener,
    required this.child,
    this.isReplayValueStream = true,
  });

  /// The [ValueStream] that the [ValueStreamConsumer] will interact with.
  final ValueStream<M> stream;
  final T? Function(M event)? distinctBy;

  /// Takes the `BuildContext` along with the `previous` and `current` values
  ///  and is responsible for executing in response to `value` changes.
  final ValueStreamWidgetListener<M, T> listener;

  /// The widget which will be rendered as a descendant of the
  /// [ValueStreamListener].
  final Widget child;

  /// Whether or not the [stream] emits the last value
  /// like [BehaviorSubject] does.
  ///
  /// Defaults to `true`.
  ///
  /// 注意:
  /// 在[FrViewModel]中, [VM.stream]是来自[BehaviorSubject]的[ValueStream]
  ///   但某些情况下, [VM.stmXxx]可能不是来自于[VM.stream], 而是单纯的[Stream],
  ///   因此需要将本值设为`false`
  final bool isReplayValueStream;

  @override
  State<ValueStreamListener<M, T>> createState() =>
      _ValueStreamListenerState<M, T>();

  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties
      ..add(DiagnosticsProperty<ValueStream<M>>('stream', stream))
      ..add(
          DiagnosticsProperty<bool>('isReplayValueStream', isReplayValueStream))
      ..add(ObjectFlagProperty<ValueStreamWidgetListener<M, T>>.has(
          'listener', listener))
      ..add(ObjectFlagProperty<Widget>.has('child', child));
  }
}

class _ValueStreamListenerState<M, T> extends State<ValueStreamListener<M, T>> {
  StreamSubscription<M>? _subscription;
  T? _preDistinct;
  T? _curDistinct;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _subscribe();
    _initialized = true;
  }

  @override
  void didUpdateWidget(covariant ValueStreamListener<M, T> oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.stream != oldWidget.stream) {
      _unsubscribe();
      _subscribe();
    }
  }

  @override
  void dispose() {
    _unsubscribe();
    super.dispose();
  }

  T _toCurDistinct(M value) => (widget.distinctBy?.call(value) ?? value) as T;

  void _subscribe() {
    final stream = widget.stream;

    if (!_initialized) {
      _curDistinct = _toCurDistinct(stream.value);
    }

    final int skipCount;

    if (widget.isReplayValueStream) {
      skipCount = _initialized ? 0 : 1;
    } else {
      skipCount = 0;
      if (_initialized) {
        _ambiguate(WidgetsBinding.instance)!.addPostFrameCallback((_) {
          _notifyListener(stream.value);
        });
      }
    }

    final streamToDistinct = skipCount > 0 ? stream.skip(skipCount) : stream;
    final streamToListen =
        streamToDistinct.map((e) => (e, _toCurDistinct(e))).distinct().map((e) {
      _preDistinct = _curDistinct;
      _curDistinct = e.$2;
      return e.$1;
    });
    _subscription = streamToListen.listen(
      (value) {
        if (!mounted) return;
        _notifyListener(value);
      },
      onError: (Object e, StackTrace s) {
        if (!mounted) return;
        setState(() {});
      },
    );
  }

  void _notifyListener(M value) =>
      widget.listener(context, _preDistinct, _curDistinct, value);

  void _unsubscribe() => _subscription?.cancel();

  @override
  Widget build(BuildContext context) => widget.child;
}

/// Reference: https://docs.flutter.dev/release/release-notes/release-notes-3.0.0#your-code
///
/// This allows a value of type T or T?
/// to be treated as a value of type T?.
///
/// We use this so that APIs that have become
/// non-nullable can still be used with `!` and `?`
/// to support older versions of the API as well.
T? _ambiguate<T>(T? value) => value;
