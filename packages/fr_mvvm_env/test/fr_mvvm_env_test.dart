import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

main() {
  test('test', () async {
    final vm = FrEnvViewModel(EnvModel(env: 'dev'), all: []);
    await vm.updateEnv(const EnvModel(env: 'prod'));
    expect(vm.value, const EnvModel(env: 'prod'));
  });
}
