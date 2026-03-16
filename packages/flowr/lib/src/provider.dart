import 'dart:developer' show log;

import 'package:flowr/src/view_model.dart' show FrViewModel;
import 'package:flowr_dart/flowr_dart.dart' show FrService;
import 'package:flutter/foundation.dart' show shortHash;
import 'package:flutter/widgets.dart'
    show BuildContext, Key, TransitionBuilder, Widget;
import 'package:get_it/get_it.dart' show GetIt, ObjectRegistrationType;
import 'package:provider/provider.dart'
    show Provider, Create, Dispose, MultiProvider, ReadContext;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;

/// - auto dispose [FrViewModel]
class FrProvider<VM extends FrService> extends Provider<VM> {
  final Function(BuildContext c, VM vm)? onCreated;

  ///
  /// [onCreated] if you want inject [VM] to other [VM] when [VM] created.
  FrProvider(
    Create<VM> create, {
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: (c) {
           final vm = create(c);
           onCreated?.call(c, vm);
           return vm;
         },
         dispose: (c, vm) {
           dispose?.call(c, vm);
           vm.dispose();
         },
       );

  /// inject [VM] from [GetIt] container to Widget tree.
  FrProvider.di({
    GetIt? di,
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: (c) {
           // VM extends FrViewModel
           final container = di ?? GetIt.I;
           final vm = container<VM>();
           onCreated?.call(c, vm);
           return vm;
         },
         dispose: (c, vm) {
           dispose?.call(c, vm);
           di ??= GetIt.I;
           final reg = di?.findFirstObjectRegistration<VM>();
           final fun = switch (reg?.registrationType) {
             null => () {},
             ObjectRegistrationType.alwaysNew => () {
               // just dispose, GetIt always return new instance
               vm.dispose();
             },
             ObjectRegistrationType.constant => () {
               log(
                 'Dev Tips: '
                 'Try use `FrProvider.di` with `lazySingleton` VM, '
                 'or `FrProvider.value` with `singleton` VM. '
                 'Because you can not auto dispose `singleton`VM [${VM.runtimeType}] by FrProvider.di',
               );
             },
             ObjectRegistrationType.lazy => () {
               // dispose and reset lazy singleton
               vm.dispose();
               di!.resetLazySingleton<VM>();
             },
             ObjectRegistrationType.cachedFactory => () {
               // just dispose, GetIt may return new instance or VM throw `StateError`
               vm.dispose();
             },
           };
           fun.call();
         },
       );

  /// use in dialog context
  FrProvider.value({
    super.key,
    required super.value,
    super.updateShouldNotify,
    super.builder,
    super.child,
    this.onCreated, // ignore
  }) : super.value();

  static FrMultiProvider multi(
    List<SingleChildWidget> providers, {
    Key? key,
    required,
    TransitionBuilder? builder,
    Widget? child,
  }) => FrMultiProvider(
    key: key,
    providers: providers,
    builder: builder,
    child: child,
  );

  /// [onlyProvider]
  ///   false: read Provider first, then DI
  ///   true: only read provider;
  ///   null: read DI first, then Provider;
  static T of<T extends Object>(
    BuildContext context, {
    bool? onlyProvider = false,
  }) {
    if (onlyProvider == false) {
      // Provider -> DI
      try {
        return Provider.of<T>(context, listen: false);
      } catch (e) {
        return _readDI<T>(nothrow: false)!;
      }
    } else if (onlyProvider == true) {
      // Provider
      return Provider.of<T>(context, listen: false);
    } else {
      // DI -> Provider
      try {
        return _readDI<T>(nothrow: false)!;
      } catch (e) {
        log(
          'Waring! `read<$T>(onlyProvider=null)` read Global first, then Provider',
          name: 'FlowR',
        );
        return Provider.of<T>(context, listen: false);
      }
    }
  }

  static T? readDI<T extends Object>({bool nothrow = false}) =>
      _readDI(nothrow: nothrow);

  static T? _readDI<T extends Object>({bool nothrow = false}) {
    if (GetIt.I.isRegistered<T>()) {
      final r = GetIt.I.get<T>();
      log(
        'FrReadContext get Global <$T>[#${shortHash(r)}] ${(r is FrViewModel) ? r.value : ''} ',
        name: 'FlowR',
      );
      return r;
    }
    if (nothrow) return null;
    throw "<$T> not register in GetIt; try `GetIt.I.registerSingleton()`";
  }

  @Deprecated('use FrProvider.di; remove at 2.0.1')
  static get container => FrProvider.di;
}

class FrMultiProvider extends MultiProvider {
  FrMultiProvider({
    super.key,
    required super.providers,
    super.builder,
    super.child,
  });
}
