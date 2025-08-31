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
///   return old..foo = 'bar';
/// });
/// ```
class SkipError extends FlowrError {
  SkipError(super.msg);
  @override
  String toString() => "SkipError($msg)";
}
