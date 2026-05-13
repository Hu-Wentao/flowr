/// Global compatibility switches for FlowR.
abstract final class FlowRCompatibility {
  /// When true, [FlowR.put] emits even when the next value is `==` the current
  /// value.
  ///
  /// This preserves the old BehaviorSubject-based behavior, including in-place
  /// model mutation followed by `put`/`update`. Set to false to use Cubit's
  /// usual equal-state suppression semantics.
  static bool emitEqualValues = false;
}
