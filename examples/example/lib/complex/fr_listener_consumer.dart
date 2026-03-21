import 'dart:developer';

import 'package:example/complex/user.mvvm.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class FrConsumerExample extends StatelessWidget {
  const FrConsumerExample({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => UserViewModel()..init(),
      child: Builder(builder: (context) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('FrConsumerExample'),
          ),
          body: FrConsumer<UserViewModel, UserModel>(
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
            buildWhen: (p, c) => p.age != c.age,
            builder: (c, s, child) => Center(
              child: Text("""
              Hello FrConsumer Example\n
              - you must return new instance in `update` method, not old..age = nAge;
                            
              // return old.copyWith(age: nAge ?? (old.age + 1));
              return UserModel(
                name: old.name,
                age: nAge ?? (old.age + 1),
              );
              ---
              And, current data is: ${s.data}
              """),
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
