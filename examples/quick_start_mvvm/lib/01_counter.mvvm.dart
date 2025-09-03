import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// 极简计数器 ViewModel

/// Model: 纯状态数据, 类型为 int

/// ViewModel: 只包含一个操作方法
class CounterVM extends FrViewModel<int> {
  @override
  final int initValue;

  // 通过构造方法设置Model的初始值
  CounterVM(this.initValue);

  // 方法: 增加计数值
  incrementCounter() async => await update((old) => old + 1);
}

/// 调用示例
example() async {
  // 创建
  final counter = CounterVM(0);
  // 更新状态
  await counter.incrementCounter();
  // 查询状态
  print('counter: ${counter.value}'); // 1
}

/// View: 绑定ViewModel, 构建UI

/// 创建全局变量 CounterVM实例
/// > 也可以存储到Provider中, 以便自动dispose, 清理状态
final vmCounter = CounterVM(42);

class CounterView extends StatelessWidget {
  const CounterView({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder(
      stream: vmCounter.stream,
      builder: (context, asyncSnapshot) {
        return OutlinedButton(
          // 点击调用ViewModel的方法
          onPressed: () => vmCounter.incrementCounter(),
          // 展示当前值
          child: Text('Count: ${asyncSnapshot.data}'),
        );
      },
    );
  }
}

main() {
  // runApp(const MaterialApp(home: CounterView()));
  runApp(
    const MaterialApp(
      home: Scaffold(body: Center(child: CounterView())),
    ),
  );
}
