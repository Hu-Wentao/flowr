import 'package:test/test.dart';

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

mixin ParrotsMx on IAnimal {
  @override
  say() => 'Parrots!';
}
mixin ParrotsWoofMx on IAnimal {
  @override
  say() => 'Woof! and ${super.say()}';
}

mixin ParrotsMeowMx on IAnimal {
  @override
  say() => 'Meow! and ${super.say()}';
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

class Parrots extends IAnimal with ParrotsMx, ParrotsWoofMx, ParrotsMeowMx {
  @override
  say() => 'Parrots says: ${super.say()}';
}

abstract class BaseAlien {
  say() => 'Alien says: 101010';
}

mixin AlienSayMx {
  say();
}
mixin AlienRobotMx on AlienSayMx {
  @override
  say() => 'AlienRobot# i am robot ## super ## ${super.say()}';
}

class AlienMachine extends BaseAlien with AlienSayMx, AlienRobotMx {
  // @override
  // say() => 'Alien says: ${super.say()}';
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
  test('what does the Parrots say?', () {
    final parrots = Parrots();
    expect(parrots.say(), 'Parrots says: Meow! and Woof! and Parrots!');
  });
  test('what does the Alien say?', () {
    final alien = AlienMachine();
    expect(alien.say(), 'AlienRobot# i am robot ## super ## Alien says: 101010');
  });
}
