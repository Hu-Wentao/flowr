import 'dart:developer';

import 'package:example/legacy/complex/user.mvvm.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class FrListenerExample extends StatelessWidget {
  const FrListenerExample({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => UserViewModel()..init(),
      child: Builder(builder: (context) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('FrListenerExample'),
          ),
          body: FrListener<UserViewModel, UserModel>(
            listener: (BuildContext context, UserModel pre, UserModel cur,
                UserViewModel vm) {
              log('message #$pre received: $cur');
              if (pre != cur) {
                ScaffoldMessenger.of(context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(SnackBar(
                      content: Text(
                    "UserModel previous: $pre\nupdated: $cur",
                  )));
              }
            },
            child: const Center(
              child: Text("""
              Hello Listener Example\n
              - you must return new instance in `update` method, not old..age = nAge;
                            
              // return old.copyWith(age: nAge ?? (old.age + 1));
              return UserModel(
                name: old.name,
                age: nAge ?? (old.age + 1),
              );"""),
            ),
          ),
          floatingActionButton: FloatingActionButton(
            onPressed: () => context.read<UserViewModel>().upAge(),
            tooltip: 'Increment',
            child: const Icon(Icons.add),
          ),
        );
      }),
    );
  }
}
