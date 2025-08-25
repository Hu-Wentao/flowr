import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class EnvModel {
  final String env; // id
  final String? name;

  const EnvModel({
    required this.env,
    this.name,
  });

  String get fullName => '$env]${name ?? ''}';

  @override
  String toString() => 'EnvModel(env: $env, name: $name)';
}

/// extends or implements [IEnvViewModel]
abstract class IEnvViewModel<M extends EnvModel> extends FrViewModel<M> {
  Iterable<M> get all;

  updateEnv(M? value) => updateRaw((old) => value ?? initValue);
}

/// simple example [IEnvViewModel]
class FrEnvViewModel extends IEnvViewModel<EnvModel> {
  FrEnvViewModel(this.initValue, {required this.all});

  @override
  final List<EnvModel> all;

  @override
  final EnvModel initValue;
}

///
/// ```dart
/// build(BuildContext context){
///   return EnvDropdownView<YourFrEnvViewModel>(),
/// }
/// ```
class EnvDropdownView<VM extends IEnvViewModel> extends StatefulWidget {
  final String itemPrefix;
  final EnvModel? init;

  const EnvDropdownView({super.key, this.init, this.itemPrefix = 'Env'});

  @override
  State<EnvDropdownView> createState() => _EnvDropdownViewState<VM>();
}

class _EnvDropdownViewState<VM extends IEnvViewModel>
    extends State<EnvDropdownView> {
  @override
  void initState() {
    context.read<VM>().updateEnv(widget.init);
    super.initState();
  }

  @override
  Widget build(BuildContext context) => FrStreamBuilder(
      vm: context.read<VM>(),
      stream: (vm) => vm.stream,
      builder: (c, s) => MenuAnchor(
        menuChildren: [
          for (final item in s.vm.all)
            RadioMenuButton<EnvModel?>(
              value: item,
              groupValue: s.data,
              onChanged: s.vm.updateEnv,
              child: Text(
                item.fullName,
                style: const TextStyle(color: Colors.black87),
              ),
            ),
        ],
        builder: (c, ctrl, _) => TextButton(
          onPressed: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
          child: Text('${widget.itemPrefix}: ${s.data?.fullName}'),
        ),
      ));
}
