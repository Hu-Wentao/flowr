# Flutter Error Boundaries

Use this reference for a Flutter app entry point that must log or report
uncaught framework, engine-dispatched, and zoned asynchronous errors. Load
`flowr-logging.md` as well when recovered errors occur inside `FlowR`,
`FlowB`, `FrViewModel`, or `FrBlocViewModel`.

## Contents

1. Boundary ownership
2. App entry pattern
3. Recovered FlowR errors
4. Guardrails
5. Verification

## Boundary Ownership

Keep the boundaries complementary:

- Use `FlutterError.onError` for uncaught Flutter framework callback errors.
- Use `PlatformDispatcher.instance.onError` for uncaught errors dispatched by
  the Flutter engine outside framework callbacks.
- Use `runZonedGuarded` as the current isolate and zone fallback.
- Log an error consumed by a local recovery `catch` at that catch site with
  `logE`; no global boundary can observe an error after local code consumes it.
- Install separate error forwarding for child isolates.

Do not report the same error directly and then forward it into another
reporting boundary. Give each boundary one path to the shared reporter.

## App Entry Pattern

Install Flutter handlers inside the guarded zone and initialize the Flutter
binding in the same zone that later calls `runApp`.

```dart
import 'dart:async';
import 'dart:ui';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

enum AppErrorSource {
  flutterFramework,
  platformDispatcher,
  zone,
}

typedef AppErrorReporter =
    FutureOr<void> Function(
      Object error,
      StackTrace stackTrace,
      AppErrorSource source,
    );

Future<void> main() async {
  final appFuture = runZonedGuarded<Future<void>>(
    () async {
      WidgetsFlutterBinding.ensureInitialized();
      _installGlobalErrorHandlers(reportError);

      FrConfig.initialize(logLevel: Level.ALL);
      await startApplication();
    },
    (error, stackTrace) => _reportSafely(
      reportError,
      error,
      stackTrace,
      AppErrorSource.zone,
    ),
  );

  if (appFuture != null) await appFuture;
}

void _installGlobalErrorHandlers(AppErrorReporter reporter) {
  FlutterError.onError = (details) {
    if (kDebugMode) FlutterError.presentError(details);

    _reportSafely(
      reporter,
      details.exception,
      details.stack ?? StackTrace.current,
      AppErrorSource.flutterFramework,
      alreadyPrintedInDebug: true,
    );
  };

  PlatformDispatcher.instance.onError = (error, stackTrace) {
    _reportSafely(
      reporter,
      error,
      stackTrace,
      AppErrorSource.platformDispatcher,
    );
    return true;
  };
}

void _reportSafely(
  AppErrorReporter reporter,
  Object error,
  StackTrace stackTrace,
  AppErrorSource source, {
  bool alreadyPrintedInDebug = false,
}) {
  if (kDebugMode && !alreadyPrintedInDebug) {
    debugPrint(
      'Unhandled application error [$source]\n'
      '$error\n'
      '$stackTrace',
    );
  }

  unawaited(
    Future<void>.sync(
      () => reporter(error, stackTrace, source),
    ).catchError((Object reportingError, StackTrace reportingStack) {
      if (kDebugMode) {
        debugPrint(
          'Exception reporting failed [$source]\n'
          '$reportingError\n'
          '$reportingStack',
        );
      }
    }),
  );
}
```

Adapt `reportError` and `startApplication` to the app. Keep preview, test,
consent, environment, and remote-reporting policy inside `reportError`; do not
scatter those decisions across the three boundaries.

If the reporter must complete before a fatal initialization exits, expose and
await a dedicated startup-failure path instead of relying on the fire-and-forget
runtime reporter.

## Recovered FlowR Errors

Preserve the existing recovery result and log before it:

```dart
try {
  await repository.refresh();
} catch (error, stackTrace) {
  logE(
    'refresh failed',
    error: error,
    stackTrace: stackTrace,
  );
  put(state.copyWith(error: error.toString()));
}
```

Use `putError(error, stackTrace)` instead when the failure should also reach the
bloc or cubit error channel. Do not both call `logE` and `putError` for the same
failure unless duplicate logging is explicitly intended.

## Guardrails

- Do not declare `FlutterError.onError` as `async`; Flutter does not await it.
- Never force-unwrap `FlutterErrorDetails.stack`.
- Return `true` from `PlatformDispatcher.instance.onError` only after accepting
  responsibility for the error.
- Contain synchronous and asynchronous reporter failures so telemetry cannot
  create a recursive unhandled-error loop.
- Decide whether debug builds report remotely. Keep console presentation and
  remote-reporting policy separate.
- Treat overwriting global handlers as application-composition ownership. If a
  crash SDK already owns a handler, compose deliberately or select one owner.
- Do not expect the current zone to receive errors from another isolate.

## Verification

Use focused tests with an injected reporter:

1. Save the previous `FlutterError.onError` and
   `PlatformDispatcher.instance.onError`.
2. Install the handlers and restore both with test teardown.
3. Invoke `FlutterError.onError` with a null stack and verify the reporter
   receives a non-null replacement stack.
4. Invoke `PlatformDispatcher.instance.onError` and verify it returns `true`
   and reports the original error and stack.
5. Throw an asynchronous error inside the guarded zone and verify the zone
   source is reported.
6. Make the reporter fail synchronously and asynchronously; verify the failure
   is contained.
7. Test a representative local recovery catch separately and verify `logE`
   retains the original error and stack while state recovery still occurs.
