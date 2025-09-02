import 'package:injectable/injectable.dart';

class IBar {}

// class Bar extends IBar {}

class BarImpl extends IBar {}

class IFoo<T extends IBar> {}

class FooBar extends IFoo<BarImpl> {}

@module
abstract class TestModuleGen {
  /// ref https://github.com/Milad-Akarie/injectable/issues/513
  /// can not reg 'IFoo<IBar>' but get 'IFoo<BarImpl>'
  @LazySingleton(as: IFoo<IBar>)
  FooBar foo() => FooBar();
  // IFoo<IBar> foo() => FooBar();
}
