import 'package:freezed_annotation/freezed_annotation.dart';

/// Recommended Freezed preset for DTOs that participate in fr_acdd extraction.
// ignore: constant_identifier_names
const FrAcddFreezed = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
);
