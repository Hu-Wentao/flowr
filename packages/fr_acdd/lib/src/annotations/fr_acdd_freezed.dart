import 'package:freezed_annotation/freezed_annotation.dart';

/// Recommended minimal Freezed preset for DTOs that participate in fr_acdd
/// extraction.
///
/// This preset intentionally leaves `fromJson/toJson` disabled. If the DTO
/// also crosses a runtime JSON boundary, use an explicit `@Freezed(...)`
/// configuration instead and keep `@FrAcddDto` on the class.
// ignore: constant_identifier_names
const FrAcddFreezed = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
);
