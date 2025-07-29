import 'dart:developer';

import 'package:example/complex/user.mvvm.dart';
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
          body: FrListener<UserModel, String>(
            stream: context.read<UserViewModel>().stream,
            distinctBy: (e) => e.name,
            listener: (BuildContext context, previous, current, value) {
              log('message #$previous received: $current');
              if (previous != current) {
                ScaffoldMessenger.of(context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(SnackBar(
                      content: Text(
                    "UserModel previous: $previous\nupdated: $current",
                  )));
              }
            },
            child: const Center(
              child: Text("""
              Hello Listener Example\n
              - you must return new instance in `update` method, not old..age = nAge;
                            
              // return old..age = nAge ?? (old.age + 1);
              return UserModel(
                name: old.name,
                age: nAge ?? (old.age + 1),
              );"""),
            ),
          ),
          floatingActionButton: FloatingActionButton(
            onPressed: () => context.read<UserViewModel>().updateAge(),
            tooltip: 'Increment',
            child: const Icon(Icons.add),
          ),
        );
      }),
    );
  }
}
