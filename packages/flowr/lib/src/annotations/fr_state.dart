import 'package:freezed_annotation/freezed_annotation.dart';
export 'package:freezed_annotation/freezed_annotation.dart' show Default;

/// Recommended Freezed preset for page-local immutable state that should be
/// easy to inspect in logs and debug tools.
///
/// This enables `toJson()` for snapshotting state, but keeps `fromJson()`
/// disabled so ordinary UI state does not implicitly claim restore semantics.
// ignore: constant_identifier_names
const FrState = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: true,
);

/// Recommended Freezed preset for page-local immutable state that must be
/// restored from serialized JSON, such as persisted or recoverable UI state.
///
/// Use this only when the state class genuinely needs `fromJson()` in
/// addition to debug-friendly `toJson()`.
// ignore: constant_identifier_names
const FrStateJson = Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: true,
  toJson: true,
);
