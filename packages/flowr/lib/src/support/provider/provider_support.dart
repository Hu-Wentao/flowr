import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/src/mixin/change_notifier.dart';
import 'package:flutter/foundation.dart';

/// support Provider-Consumer
/// adapt ChangeNotifierProvider use ChangeNotifier
abstract class FrChangeNotifierVM<M extends FrModel> extends FrViewModel<M>
    with ChangeNotifier, FrChangeNotifierMx {}
