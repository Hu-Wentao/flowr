import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class EnvModel {
  final String env; // id

  const EnvModel({required this.env});

  @override
  String toString() => 'EnvModel(env: $env)';
}

/// extends or implements [IEnvViewModel]
abstract class IEnvViewModel<M extends EnvModel> extends FrViewModel<M> {
  Iterable<M> get all;

  updateEnv(M? value) => update((old) {
    skpIfNull(value, 'skip update null env');
    return value!;
  });
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
///FrProvider(
///  (context) => YourFrEnvViewModel(),
///  child: MaterialApp(
///    home: EnvDropdownView<YourFrEnvViewModel, EnvModel>(),
///    ),
///  ),
///),
/// ```
class EnvDropdownView<VM extends IEnvViewModel<M>, M extends EnvModel>
    extends StatefulWidget {
  final M? init;
  final Widget Function(BuildContext c, MenuController ctrl, M? env)? buildBtn;
  final Widget Function(BuildContext c, M? env)? buildAnchorTile;

  const EnvDropdownView({
    super.key,
    this.init,
    this.buildBtn,
    this.buildAnchorTile,
  });

  @override
  State<EnvDropdownView> createState() => _EnvDropdownViewState<VM, M>();
}

class _EnvDropdownViewState<VM extends IEnvViewModel<M>, M extends EnvModel>
    extends State<EnvDropdownView<VM, M>> {
  @override
  void initState() {
    context.read<VM>().updateEnv(widget.init);
    super.initState();
  }

  @override
  Widget build(BuildContext context) => FrStreamBuilder(
    vm: context.read<VM>(),
    stream: (vm) => vm.stream,
    builder:
        (c, s) => MenuAnchor(
          builder:
              (c, ctrl, _) =>
                  widget.buildBtn?.call(c, ctrl, s.data) ??
                  OutlinedButton(
                    onPressed: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
                    child: Text('${s.data}'),
                  ),
          menuChildren: [
            for (final item in s.vm.all)
              RadioMenuButton<M>(
                value: item,
                groupValue: s.data,
                onChanged: s.vm.updateEnv,
                child:
                    widget.buildAnchorTile?.call(c, s.data) ??
                    Text(
                      '$item',
                      style: const TextStyle(color: Colors.black87),
                    ),
              ),
          ],
        ),
  );
}
