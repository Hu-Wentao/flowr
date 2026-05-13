## 2.13.0 2026-05-13
* **Breaking Change**: `FrConfig.emitEqualValues` now defaults to `false`, so `FlowR.put(value)` follows Cubit's equal-state suppression semantics and will not emit when `value == currentValue`.
* refactor: replace rxdart with bloc
* refactor: config layering for flowr dart
* **Migration**: if an app depends on the old BehaviorSubject behavior where equal values still notify listeners, call `FrConfig.initialize(emitEqualValues: true)` explicitly.

## 2.12.0 2026-05-10
* feat: LoggableMx add logW and logE
* refactor flowr_dart; doc Readme.md

## 2.11.2 2026-04-17
* Merge branch 'feat-all_log_when_put'
* fix loggable.dart log print
* fix put&logging order

## 2.11.1 2026-03-25
* fix Flowr::logger set this.logExtra, auto show invoke method name

## 2.11.0 2026-03-20
* fix LoggableMx ::logger print method name; depre ::frPrint
* fix ::runCatching remove 'ignoreSkipError'
* feat SkipError,::skpIf,::skpNull add 'level',
* doc

## 2.10.2 2026-03-19
* fix(loggable) ::devLogRecordPrinter, when r.object not LogExtra

## 2.10.1 2026-03-19
* remove debug code

## 2.10.0 2026-03-18
* fix doc/test
* refactor LoggableMx use package:logging; feat LoggableMx ::logF (Fine), ::logI (Info), ::logS (Shout)

## 2.9.4 2026-03-17
* fix **important** `runCatching` process `SkipError` when use `slowly`

## 2.9.3 2026-03-16
* fix **important** `distinctBy` correctly de-duplicate based on selected field, even if the source object identity changes (e.g. `copyWith` for final model).
* fix **important** `_DistinctValueStream` consistency: cache the latest emitted value from the filtered stream.
* feat `distinctBy` correctly captures field value for mutable objects during emission.

## 2.9.2 2026-03-04
* fix SlowlyMx ref
* update slowly to ^0.4.3

## 2.9.1 2026-03-03
* fix SlowlyMx with DisposeMx

## 2.9.0 2026-03-03
* feat **important** add `SlowlyMx` for debounce, throttle, and mutex (powered by `slowly` ^0.4.1)
* refactor **important** `RunCatchingMx`: move slowly logic into `runCatching` for unified scheduling.
* refactor `UpdatableMx`: simplify `update` by delegating to `runCatching`.

## 2.8.0 2026-02-24
* refactor: replace _put with putWithLogging for improved logging
* feat(FlowR) ::use 'logging' replace 'onPutLogging'

## 2.7.1 2026-02-03 **replaced by 2.8.0**
* feat(FlowR) ::update 'onPutLogging' add 'prv' param, dev can get prv Model event  
  (In the case of creating a new Event instead of reusing an old Event)

## 2.7.0 2026-02-03
* feat(FlowR) ::update add 'onPutLogging'. dev can change log content when call FlowR::update.

## 2.6.0 2026-01-05
* feat(WhereValueX) ::whereValue

## 2.5.0 2025-12-30
* feat(::logger) print location(StackTrace Frames) will exclude 'flutter' package

## 2.4.3 2025-12-24
* refactor(::runCatching): logger print 'SKIPPED:'

## 2.4.2 2025-12-22
* refactor(SubsAutoDisposeMx) now on DisposeMx, not IService

## 2.4.1 2025-12-19
* fix(::runCatching) can't catch SkipError

## 2.4.0 2025-12-17
* remove **important** SlowlyMx: deprecated 'slowlyMs','debounceTag','throttleTag';
* fix **important** UpdatableMx: Fixed the issue where `update` could not be called synchronously.

## 2.3.0 2025-10-28
* feat **important** FrService/IService/FlowRMx

## 2.2.0 2025-9-3
* feat ::runCatching.block can return null; (for return ::update)

## 2.1.2 2025-9-2
* fix **important** SubsAutoDisposeMx::dispose, old version can not dispose StreamSubscription correctly.

## 2.1.1 2025-9-1
* feat 
 - FlowrError,SkipError impl toString;
 - ::runCatching will print SkipError

## 2.1.0 2025-8-31
* feat 
 - ::skpNull, deprecated ::skpIfNull
 - ::put add logger;
* refactor 
  - flowr_dart with 'meta', add annotation to mixin; 
  - Deprecated ::debounceMs;
* remove FlowR::updateOrNull

* fix LoggableMx::logger's LogExtra frames print; 

## 2.0.0 2025-8-29
* retract v1.3.0 , re publish as v2.0.0 
 - ::updateRaw -> ::update is break change

## 1.3.0 2025-8-28 
* feat 
  - ::update 'update' can not return null;
  - ::skpIf, ::skpNull
  - use `throw SkipError('reason');` or `skpIf(true, 'reason...');` interrupt `::update`
* refactor deprecation UpdatableMx ::updateRaw 
  replace with ::update

## 1.2.0 2025-8-27
* feat FlowrError; SkipError; ::runCatching/::updateRaw add 'ignoreSkipError';

## 1.1.2 2025-8-26
* update Dart ^3.7

## 1.1.1 2025-8-25
* fix ::runCatching when onSuccess ==null, can not return value;

## 1.1.0 2025-8-23
* refactor FlowR::put will return value;
* fix ::runCatching return value;

## 1.0.0 2025-8-23
* Split pure dart part form [FlowR](https://github.com/Hu-Wentao/flowr)
