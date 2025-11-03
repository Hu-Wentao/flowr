/// for some !kReleaseModel only code
/// when [msg] !=null, will use [fn] result
void assertRun(bool? Function() fn, {String? msg}) {
  assert(
    (() {
      if (msg != null) return fn.call() ?? true;
      return true;
    })(),
    msg,
  );
}
