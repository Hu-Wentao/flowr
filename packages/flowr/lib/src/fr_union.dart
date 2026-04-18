import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/src/view/value_stream_widget.dart'
    show ValueStreamBuilder;
import 'package:flutter/widgets.dart';

typedef FrUnionModel = Object; // 不允许为null

/// 平铺状态, 可通过命名叠加来区分层级
class FrUnion {
  final Map<String, FrUnionModel> initials;
  final Map<String, FrUnionModel> value;

  FrUnion.build({required this.initials, required this.value});

  factory FrUnion(Set<FrUnionModel> models) =>
      FrUnion.ofTag({for (var initM in models) ('', initM)});

  factory FrUnion.ofTag(Set<(String, FrUnionModel)> tagModels) {
    final initials = {
      for (var initTM in tagModels)
        modelKeyByValue(tag: initTM.$1, value: initTM.$2): initTM.$2,
    };
    return FrUnion.build(initials: initials, value: {...initials});
  }

  static String modelKey<M>({String tag = ''}) => '$M##$tag';

  static String modelKeyByValue<M>({required String tag, required M value}) =>
      '${value.runtimeType}##$tag';

  M modelValue<M>(String tag) {
    final k = modelKey<M>(tag: tag);
    return (value[k] as M?) ??
        (initials[k] as M?) ??
        (throw """
Must set init value from `FrUnion` for type[$M] !

example:
```dart
FrUnionViewModel({
  CounterM(0),
  UserM('Mike', 18),
})
```
        """);
  }

  FrUnion copyWith(Map<String, FrUnionModel> value) => FrUnion.build(
    initials: initials,
    value: {...initials, ...this.value, ...value},
  );
}

/// 提供一个全局VM, 用于简化代码.
/// ⚠️ 单一全局VM不适用于复杂应用场景, 跨app复用状态可能造成不可预知的错误
/// 与M对应的VM方法,请考虑通过 extension 封装
class FrUnionViewModel extends FrViewModel<FrUnion> {
  @override
  final FrUnion initValue;

  FrUnionViewModel.build(this.initValue);

  factory FrUnionViewModel(Set<FrUnionModel> models) =>
      FrUnionViewModel.build(FrUnion(models));

  factory FrUnionViewModel.ofTag(Set<(String, FrUnionModel)> tagModels) =>
      FrUnionViewModel.build(FrUnion.ofTag(tagModels));

  ValueStream<M> streamBy<M>({String tag = ''}) =>
      stream.distinctWith((e) => e.modelValue<M>(tag));

  FutureOr<M?> updateBy<M>(
    FutureOr<M> Function(M old) updater, {
    String tag = '',
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
    OnLogging<M>? logging,
  }) {
    final rst = update(
      (old) {
        final r = updater(old.modelValue<M>(tag));
        if (r is Future<M>) {
          return r.then(
            (r) => old.copyWith({
              FrUnion.modelKey<M>(tag: tag): r as FrUnionModel,
            }),
          );
        } else {
          return old.copyWith({
            FrUnion.modelKey<M>(tag: tag): r as FrUnionModel,
          });
        }
      },
      onError: onError,
      slowlyMs: slowlyMs,
      debounceTag: debounceTag,
      throttleTag: throttleTag,
      mutexTag: mutexTag,
      logging:
          logging == null
              ? null
              : (previous, current) => logging.call(
                previous.modelValue<M>(tag),
                current.modelValue<M>(tag),
              ),
    );
    if (rst is Future<FrUnion>) {
      return rst.then((r) => r.modelValue<M>(tag));
    } else if (rst is FrUnion) {
      return rst.modelValue<M>(tag);
    } else {
      return null;
    }
  }
}

/// 用于从[FrUnionViewModel] 读取特定状态
class FrViewU<M extends FrUnionModel> extends StatelessWidget {
  final FrViewBuilder<FrUnionViewModel, M> builder;

  /// false: read Provider first, then Global
  /// true: only read provider;
  /// null: read Global first, then Provider;
  final bool? onlyProvider;

  /// Optional [buildWhen] to control rebuilds.
  final bool Function(M pre, M cur)? buildWhen;
  final String tag;
  final Widget? child;

  const FrViewU({
    super.key,
    this.tag = '',
    this.onlyProvider = false,
    this.buildWhen,
    required this.builder,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    final vm = context.read<FrUnionViewModel>(onlyProvider: onlyProvider);
    return ValueStreamBuilder<M>(
      stream: vm.streamBy<M>(tag: tag),
      buildWhen: buildWhen,
      child: child,
      builder: (BuildContext context, M m, Widget? child) {
        return builder(context, (vm: vm, data: m), child);
      },
    );
  }
}
