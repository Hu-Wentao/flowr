import 'package:flowr/flowr_mvvm.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('FrState exposes the debug-state preset', () {
    expect(FrState, isA<Freezed>());
    expect(FrState.copyWith, isTrue);
    expect(FrState.equal, isTrue);
    expect(FrState.toStringOverride, isTrue);
    expect(FrState.fromJson, isFalse);
    expect(FrState.toJson, isTrue);
  });

  test('FrStateJson exposes the restorable-state preset', () {
    expect(FrStateJson, isA<Freezed>());
    expect(FrStateJson.copyWith, isTrue);
    expect(FrStateJson.equal, isTrue);
    expect(FrStateJson.toStringOverride, isTrue);
    expect(FrStateJson.fromJson, isTrue);
    expect(FrStateJson.toJson, isTrue);
  });
}
