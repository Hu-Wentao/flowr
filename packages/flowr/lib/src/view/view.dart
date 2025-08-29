import 'dart:async';

import 'package:flowr/src/mixin/auto_dispose.dart';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:rxdart/rxdart.dart';

import 'package:flowr/src/mixin.dart';

part './value_stream_listener.dart';

part './value_stream_builder.dart';

part './value_stream_consumer.dart';

typedef FrListener<M, T> = ValueStreamListener<M, T>;

///
/// use 'autoDispose' to register 'StreamSubscription's
/// when page call 'dispose', will call 'disposeAuto' to cancel all subscriptions
@Deprecated('will remove at 2.0.1')
mixin FrPageMx<T extends StatefulWidget>
    on State<T>, SubsAutoDisposeMx, NtfAutoDisposeMx {}
