import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';

typedef FrUnionModel = Object; // 不允许为null
typedef TaggedUnionModel = (FrUnionModel, String); // <model, tag>

/// 平铺状态, 可通过命名叠加来区分层级
class FrUnion {
  final Map<String, FrUnionModel> initials;
  final Map<String, FrUnionModel> value;

  const FrUnion.build({required this.initials, required this.value});

  factory FrUnion.ofModel(Set<FrUnionModel> models) =>
      FrUnion.ofTaggedModel({for (var initM in models) (initM, '')});

  /// use '' for default tag
  /// ```dart
  /// FrUnion.ofTaggedModel({
  ///    (UserM('Mike', 18), ''),
  ///    (UserM('Mike2', 19), 'tag2'),
  ///  })
  /// ```
  factory FrUnion.ofTaggedModel(Set<TaggedUnionModel> tagModels) {
    final initials = {
      for (var initTM in tagModels)
        modelKeyByValue(value: initTM.$1, tag: initTM.$2): initTM.$1,
    };
    return FrUnion.build(initials: initials, value: {...initials});
  }

  /// support [FrUnion.ofModel] & [FrUnion.ofTaggedModel]
  static FrUnion of<T extends Object>(Set<T> models) {
    final taggedModels = models.whereType<TaggedUnionModel>().toSet();

    if (taggedModels.isEmpty) {
      return FrUnion.ofModel(models.cast<FrUnionModel>().toSet());
    }

    if (taggedModels.length == models.length) {
      return FrUnion.ofTaggedModel(taggedModels);
    }

    throw ArgumentError.value(
      models,
      'models',
      'FrUnion.of expects either model values or tagged model tuples.',
    );
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
  FrUnionViewModel.build(super.initialState);

  factory FrUnionViewModel(Set<FrUnionModel> models) =>
      FrUnionViewModel.build(FrUnion.of(models));

  factory FrUnionViewModel.ofTag(Set<TaggedUnionModel> tagModels) =>
      FrUnionViewModel.build(FrUnion.ofTaggedModel(tagModels));

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
    return ValueStreamBuilder<FrUnion>(
      stream: vm.valueStream,
      buildWhen: (previous, current) {
        final previousValue = previous.modelValue<M>(tag);
        final currentValue = current.modelValue<M>(tag);
        return buildWhen?.call(previousValue, currentValue) ??
            previousValue != currentValue;
      },
      child: child,
      builder: (BuildContext context, FrUnion union, Widget? child) {
        final m = union.modelValue<M>(tag);
        return builder(context, (vm: vm, data: m), child);
      },
    );
  }
}
