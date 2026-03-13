import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class ConcurrencyVM extends FrViewModel<int> {
  @override
  int get initValue => 0;

  ConcurrencyVM();

  // 1. Mutex (Exhaust)
  // Clicking multiple times during execution will ignore subsequent calls.
  Future<void> addWithMutex() async {
    await update(
      (old) async {
        logger('Mutex: start');
        await Future.delayed(const Duration(seconds: 1));
        logger('Mutex: end');
        return old + 1;
      },
      mutexTag: 'add',
    );
  }

  // 2. Debounce
  // Only the last call after 500ms of inactivity will execute.
  void addWithDebounce() {
    update(
      (old) {
        logger('Debounce: execute');
        return old + 1;
      },
      debounceTag: 'add',
      slowlyMs: 500,
    );
  }

  // 3. Throttle
  // Executed at most once every 500ms.
  void addWithThrottle() {
    update(
      (old) {
        logger('Throttle: execute');
        return old + 1;
      },
      throttleTag: 'add',
      slowlyMs: 500,
    );
  }
}

class ConcurrencyView extends StatelessWidget {
  const ConcurrencyView({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => ConcurrencyVM(),
      child: Builder(
        builder: (context) {
          final vm = context.read<ConcurrencyVM>();
          return Scaffold(
            appBar: AppBar(title: const Text('FlowR Concurrency Demo')),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  StreamBuilder<int>(
                    stream: vm.stream,
                    builder: (context, snapshot) {
                      return Text(
                        'Count: ${snapshot.data}',
                        style: Theme.of(context).textTheme.headlineLarge,
                      );
                    },
                  ),
                  const SizedBox(height: 40),
                  ElevatedButton(
                    onPressed: () => vm.addWithMutex(),
                    child: const Text('Add with Mutex (1s lock)'),
                  ),
                  ElevatedButton(
                    onPressed: () => vm.addWithDebounce(),
                    child: const Text('Add with Debounce (500ms)'),
                  ),
                  ElevatedButton(
                    onPressed: () => vm.addWithThrottle(),
                    child: const Text('Add with Throttle (500ms)'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

void main() {
  runApp(const MaterialApp(home: ConcurrencyView()));
}
