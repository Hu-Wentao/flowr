import 'package:flutter_test/flutter_test.dart';

abstract class IAnimal {
  say();
}

mixin CaninesMx on IAnimal {
  @override
  say() => 'Woof!';
}
mixin FelinesMx on IAnimal {
  @override
  say() => 'Meow!';
}

mixin SeagullsMx on IAnimal, CaninesMx {
  @override
  say() => 'Squawk!, ${super.say()}';
}

class Dog extends IAnimal with CaninesMx {
  @override
  say() => 'Dog says: ${super.say()}';
}

class Fox extends IAnimal with CaninesMx, FelinesMx {
  @override
  say() => 'Fox says: ${super.say()}';
}

// class Seagull extends IAnimal with CaninesMx, SeagullsMx {
class Seagull extends IAnimal with CaninesMx, SeagullsMx {
  @override
  say() => 'Seagull says: ${super.say()}';
}

main() {
  test('mixin', () {
    final dog = Dog();
    expect(dog.say(), 'Dog says: Woof!');
  });

  test('what does the fox say?', () {
    final fot = Fox();
    expect(fot.say(), 'Fox says: Meow!');
  });

  test('what does the Seagull say?', () {
    final seagull = Seagull();
    expect(seagull.say(), 'Seagull says: Squawk!, Woof!');
  });
}
