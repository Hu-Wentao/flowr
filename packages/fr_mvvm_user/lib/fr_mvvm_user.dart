import 'dart:async' show FutureOr;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class UserModel {
  final String userId;
  final String? token;

  const UserModel({this.userId = '', this.token});

  @override
  String toString() => 'UserModel($userId)';
}

/// extends or implements [IUserViewModel]
abstract class IUserViewModel<M extends UserModel> extends FrViewModel<M> {
  IUserViewModel(super.initialState);

  /// [user]: M
  ///   if null, cancel update
  FutureOr<M?> updateUser(M? user) => update((old) => skpNull(user, 'user'));
}

/// simple example [IUserViewModel]
class FrUserViewModel extends IUserViewModel<UserModel> {
  FrUserViewModel(super.initialState);
}

///
/// ```dart
///FrProvider(
///  (context) => FrUserViewModel(),
///  child: MaterialApp(
///    home: FrUserDropdownView<FrUserViewModel, UserModel>(),
///    ),
///  ),
///),
/// ```
class FrUserDropdownView<VM extends IUserViewModel<M>, M extends UserModel>
    extends StatefulWidget {
  final M? init;
  final Widget Function(BuildContext c, MenuController ctrl, M? m)? buildBtn;
  final Widget Function(BuildContext c, M? m)? buildAnchorTile;
  final List<M> options;

  const FrUserDropdownView({
    super.key,
    this.init,
    this.buildBtn,
    this.buildAnchorTile,
    this.options = const [],
  });

  @override
  State<FrUserDropdownView> createState() => _FrUserDropdownViewState<VM, M>();
}

class _FrUserDropdownViewState<
  VM extends IUserViewModel<M>,
  M extends UserModel
>
    extends State<FrUserDropdownView<VM, M>> {
  @override
  void initState() {
    if (widget.init != null) context.read<VM>().updateUser(widget.init);
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
                    child: Text('${s.data}'),
                  ),
          menuChildren: [
            for (final item in widget.options)
              RadioMenuButton<M>(
                value: item,
                groupValue: s.data,
                onChanged: s.vm.updateUser,
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
