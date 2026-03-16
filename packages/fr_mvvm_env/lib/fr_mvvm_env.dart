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

  /// [env]: M
  ///   if null, cancel update
  updateEnv(M? env) => update((old) => skpNull(env, 'env'));
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
///    home:FrEnvDropdownView<YourFrEnvViewModel, EnvModel>(),
///    ),
///  ),
///),
/// ```
class FrEnvDropdownView<VM extends IEnvViewModel<M>, M extends EnvModel>
    extends StatefulWidget {
  final M? init;
  final Widget Function(BuildContext c, MenuController ctrl, M? m)? buildBtn;
  final Widget Function(BuildContext c, M? m)? buildAnchorTile;

  const FrEnvDropdownView({
    super.key,
    this.init,
    this.buildBtn,
    this.buildAnchorTile,
  });

  @override
  State<FrEnvDropdownView> createState() => _FrEnvDropdownViewState<VM, M>();
}

class _FrEnvDropdownViewState<VM extends IEnvViewModel<M>, M extends EnvModel>
    extends State<FrEnvDropdownView<VM, M>> {
  @override
  void initState() {
    if (widget.init != null) context.read<VM>().updateEnv(widget.init);
    super.initState();
  }

  @override
  Widget build(BuildContext context) => FrView<VM, M>(
    builder:
        (c, s, _) => MenuAnchor(
          builder:
              (c, ctrl, _) =>
                  widget.buildBtn?.call(c, ctrl, s.data) ??
                  OutlinedButton(
                    onPressed: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
                    child: Tooltip(
                      message: '${s.data}',
                      child: Text('${s.data?.env}'),
                    ),
                  ),
          menuChildren: [
            for (final item in s.vm.all)
              RadioMenuButton<M>(
                value: item,
                groupValue: s.data,
                onChanged: s.vm.updateEnv,
                child:
                    widget.buildAnchorTile?.call(c, s.data) ??
                    Tooltip(
                      message: '${s.data}',
                      child: Text(
                        item.env,
                        style: const TextStyle(color: Colors.black87),
                      ),
                    ),
              ),
          ],
        ),
  );
}

@Deprecated('use "FrEnvDropdownView"')
typedef EnvDropdownView = FrEnvDropdownView;
