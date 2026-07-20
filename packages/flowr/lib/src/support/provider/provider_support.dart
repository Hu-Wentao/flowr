import 'package:flowr/src/mixin/change_notifier.dart';
import 'package:flowr/src/model.dart' show FrModel;
import 'package:flowr/src/view_model.dart' show FrViewModel;
import 'package:flutter/foundation.dart';

/// support Provider-Consumer
/// adapt FrProvider.listenable use ChangeNotifier
abstract class FrChangeNotifierVM<M extends FrModel> extends FrViewModel<M>
    with ChangeNotifier, FrChangeNotifierMx {
  FrChangeNotifierVM(super.initialState);
}
