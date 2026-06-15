import 'package:freezed_annotation/freezed_annotation.dart';

/// Recommended minimal Freezed preset for DTOs that participate in fr_acdd
/// extraction.
///
/// This preset intentionally leaves `fromJson/toJson` disabled. If the DTO
/// also crosses a runtime JSON boundary, prefer `FrAcddFreezedJSON`. Use an
/// explicit `@Freezed(...)` configuration only when the DTO needs custom
/// Freezed options beyond the preset.
// ignore: constant_identifier_names
const FrAcddFreezed = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
);

/// Recommended Freezed preset for extractable DTOs that also need runtime JSON
/// serialization.
///
/// This only enables Freezed's JSON hooks. The DTO still needs the normal
/// `factory Xxx.fromJson(...)` boilerplate and a generated `.g.dart` part in
/// the owning contract library.
// ignore: constant_identifier_names
const FrAcddFreezedJSON = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: true,
  toJson: true,
);
