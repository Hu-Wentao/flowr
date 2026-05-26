/// base FlowrError
abstract class FlowrError extends Error {
  final String msg;

  FlowrError(this.msg);

  @override
  String toString() => "FlowrError($msg)";
}

/// throw [SkipError], for break FlowR.update flowr
/// ```dart
/// update((old){
///   if(old.foo ==null) throw SkipError('foo is null, skip update state');
///   return old.copyWith(foo: 'bar');
/// });
/// ```
/// [level] Level.FINE.value == 500
class SkipError extends FlowrError {
  final int level;
  SkipError(super.msg, {this.level = 500});
  @override
  String toString() => "SkipError(Lv$level, ($msg)";
}
