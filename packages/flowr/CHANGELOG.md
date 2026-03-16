## 3.0.3 2026-03-17
* update `flowr_dart` to `^2.9.4`
  * fix **important** `runCatching` process `SkipError` when use `slowly`

## 3.0.2 2026-03-16
* update `flowr_dart` to `^2.9.3`
  * fix **important** `distinctBy` correctly de-duplicate based on selected field.
  * fix **important** `_DistinctValueStream` consistency: cache the latest emitted value.

## 3.0.1 2026-03-16
* fix: `FrProvider.di` pull from GetIt by default (avoid `ProviderNotFoundException`)

## 3.0.0 2026-03-16
* **Breaking Change**: retract `2.6.0`, upgrade to `3.0.0`
* feat: add `FrConsumer`, `FrProvider.read`, `FrProvider.readDI`
* refactor: `FrView`, `FrListener` use `ValueStreamBuilder`
* deprecated: `FrStreamBuilder`, `FrViewFutureBuilder`, `FrFutureBuilder`

## 2.5.0 2026-03-03
* feat: update `flowr_dart` to `^2.9.0`
* feat **important** support `SlowlyMx` (debounce, throttle, mutex)

## 2.4.0 2026-02-24
* feat: replace _put with putWithLogging for improved logging
* feat FrStreamBuilder use ValueStreamBuilder
* feat(FlowR) ::update 'onPutLogging' add prv param
* feat(FlowR) ::update add 'onPutLogging'
* feat(WhereValueX) ::whereValue
* dart-v2.8.0
* feat logger print location will exclude 'flutter' package
* refactor(::runCatching): logger print 'SKIPPED:'
* refactor SubsAutoDisposeMx on DisposeMx

## 2.3.1 2025-12-19
* use flowr_dart ^2.4.1
  * fix(::runCatching) can't catch SkipError

## 2.3.0 2025-12-17
* use flowr_dart ^2.4.0
  * fix **important** UpdatableMx: Fixed the issue where `update` could not be called synchronously.
  * deprecated 'slowlyMs','debounceTag','throttleTag';

## 2.2.0 2025-10-28
* adp flowr 2.3.0 FlowRMx, FrService

## 2.1.2 2025-9-2
* fix **important** NtfAutoDisposeMx::dispose, old version can not dispose notifier correctly.

## 2.1.1 2025-8-31
* fix FrProvider.di check VM type
refactor hide FrViewModel:: debugDescribeChildren, ::toDiagnosticsNode

## 2.1.0 2025-8-31
* refactor flowr/ FrViewModel extends FlowR
* update pubspec.yaml flutter_lints ^5.0.0

## 2.0.1 2025-8-30
* fix 
  - FrViewModel::autoDispose StackOverflow Error
  - FrProvider.di check VM type

## 2.0.0 2025-8-29
* retract v1.4.0 , re publish as v2.0.0
- ::updateRaw -> ::update is **break** change
- rename FrProvider.container -> FrProvider.di

## 1.4.0 2025-8-28
* feat ::update 'update' can not return null;
  - ::update 'update' can not return null;
  - ::skpIf, ::skpNull
  - use `throw SkipError('reason');` or `skpIf(true, 'reason...');` interrupt `::update`
* refactor deprecation UpdatableMx ::updateRaw
  replace with ::update

## 1.3.0 2025-8-27
* feat ::runCatching/::updateRaw add 'ignoreSkipError';

## 1.2.2 2025-8-26
* update Dart ^3.7; flutter: ">=1.17.0"

## 1.2.1 2025-8-25
* fix FrProvider.container when auto dispose, reset VM by registrationType

## 1.2.0 2025-8-23
* refactor adp flowr_dart 1.1.0, ::put return value;
* fix ::runCatching return value;

## 1.1.0 2025-8-20
* feat FrBox.init; you need invoke `await FrBox.init()` first
* fix 
  - FrRepo::findFirst can not get correct value 
  - ::updateRaw add 'await', to show full stacktrace

## 1.0.2 2025-8-19
* feat FrRepo::create add 'ifNotExists' param, true: the record is only created if it does not exist 
* fix FrRepo::findFirst can not convert json to T
* refactor FrViewModel wrap ::runCatching

## 1.0.1 2025-8-18
* refactor 
  - get_it update to ^8.2.0
  - Flutter 3.32.5

## 1.0.0 2025-8-16
* feat 
  - add FrStorage.tmp contractor, for get FrRepo to init data
  - FrStorage add 'dbVersion','onDbVersionChange' param
* improve FrChangeNotifierMx::put 'put' first, then 'super.notifyListeners'

## 0.25.0 2025-8-14
* feat FrViewModel::updateRaw can return null, will cancel this update

## 0.24.0 2025-8-11
* feat 
  - FrChangeNotifierMx; export flowr_mvvm_support.dart
  - FrViewModel with ChangeNotifier, FrChangeNotifierMx adapt ChangeNotifierProvider/Consumer

## 0.23.0 2025-8-7
* feat 
  - DistinctWithX::distinctWith test ext_test.dart 
  - FrViewModel::logExtra will default enable when `!kReleaseMode`
* refactor FrReadContextX::read 'onlyProvider'

## 0.22.0 2025-7-30
* feat 
  - RunCatchingMx, use runCatching() in VM
  - FrStorage::init jump when _db not null; ::open add 'dir' param
* fix FrRepo::delete 
* fix UpdatableMx:: slowly fun check 
* fix ValueStreamListener::_toCurDistinct 

## 0.21.0 2025-7-29
* refactor view.dart export ValueStreamListener,ValueStreamBuilder,ValueStreamConsumer
  - ValueStreamListener/ValueStreamXxx... is now fully available
* remove FrValueStreamBuilder/FrListener

## 0.20.0 2025-7-28
* feat FrViewModel/UpdatableMx::update add 'debounceTag','throttleTag'
* feat LogExtra add 'all', LoggableMx::logger add 'DEV TIPS' 
* rename LogExtraTp->LogExtra;FrViewModel::loggerExtraTp ->::logExtra

## 0.19.3 2025-7-25
* feat updateRaw will ignore debounce when debounceMs <=0 
* feat FrStreamBuilder add DiagnosticsProperty vm?.stream.value
* fix FrPageMx::dispose
* fix DisposeMx,BaseFlowR::dispose

## 0.19.2 2025-7-23
* fix (0.19.1) FrPageMx not need extends BaseFlowR
* bug if FrPageMx on State, will not call State::dispose

## 0.19.1 2025-7-22
* fix (0.19.0) UpdatableMx::updateRaw debounce error
    
## 0.19.0 2025-7-21
* feat UpdatableMx::updateRaw add 'debounceMs','slowlyTag'
* bug: debounce error

## 0.18.1 2025-7-21
* fix adapt flutter 3.16.7

## 0.18.0 2025-7-20
* feat slowly.dart; FrViewModel::debounceMs 
* feat AutoDisposeMx::subBy;FlutterAutoDisposeMx::ntfBy; ChangeNotifierX::listen add 'where' param
* remove StorageSemImpl,TableUlIdImpl,RepoSemImpl
* rename AutoDisposeMx->SubsAutoDisposeMx remove SubsAutoDisposeMx::disposeAuto/allStreamSubscription;FlowRAutoDisposeMx; rename FlutterAutoDisposeMx->NtfAutoDisposeMx; remove NtfAutoDisposeMx::disposeAuto/allNotifier refactor FrPageMx refactor FrViewModel test dart_mixin_test.dart 
* rename IStorageConfig -> IStorage; FrStorage ...

## 0.17.0 2025-7-19
* feat _MapValueStream,_DistinctValueStream 
* feat FlutterAutoDisposeMx dispose ChangeNotifier ; ChangeNotifierX
* refactor FrListener, FrValueStreamBuilder

## 0.16.0 2025-7-17
* feat DistinctByValueX distinctBy 
* feat flowr_arch.dart:
    IStorageConfig,ITable,IRepo, 
    FrRepo<T> FrStorageConfig,FrTable
* rename LogInfoTp->LogExtraTp; rename FrViewModel::loggerExtraTp 
* export rxdart.DoExtensions 

## 0.15.0 2025-7-16
* feat DistinctByX 
  stream.distinctBy()
* feat FrViewModel::logger has default
* export rxdart::DebounceExtensions
  stream.debounce()
  stream.debounceTime()

## 0.14.0 2025-7-15
* feat FlutterAutoDisposeMx
  FrViewModel::autoDisposeNotifier
* feat TestLoggableMx; export mixin.dart
* feat FrStreamBuilder add debugProperties vm,stream

## 0.13.0 2025-7-13
* feat FrProvider.container inject [VM] from [GetIt] container to Widget tree. 
* feat FrViewModel 'stream' to field 
* feat FrViewModel/UpdatableMx::updateRaw will return T?

## 0.12.0 2025-7-9
* feat FrStreamBuilder add initialData 
* export (flowr_mvvm.dart) SwitchMapExtension:: switchMap

## 0.11.2 2025-7-4
* fix FrReadContextX read error
* fix ModelSnapshot state error

## 0.11.0 2025-7-4
* feat map_value.dart,MapValueX
* feat FrReadContextX can read any type
* feat flowr_mvvm.dart export ConnectableStreamExtensions(shareValue, publishValue ...)
* remove FrStreamBuilder.diFirst
* fix LoggableMx log frame max index is len-1
* fix FrStreamBuilder ModelSnapshot can't set null data (when init);

## 0.10.0 2025-7-3
* feat LoggableMx print stacktrace info 
* feat LoggableMx.frPrint override for other log output 
* feat UpdatableMx.updateRaw can update sync; 
* remove UpdatableMx.updateOrNull 
* remove BaseFlowR.valueOrNull

## 0.9.0 2025-7-2
* feat FrViewModel.logger add caller name and invoke uri

## 0.8.0 2025-6-28
* feat export rxdart WhereNotNullExtension 
* feat AutoDisposeMx autoDispose add 'tag' param; can use nullable param; add allStreamSubscription 

## 0.7.0 2025-6-24
* remove FrView.T, `FrView<VM extends FrViewModel, M extends FrModel>`

## 0.6.0 2025-6-16
* feat view.dart FrPageMx, 
* fix provide `autoDispose` method

## 0.5.0 2025-6-16
* feat PageAutoDisposeMx
* feat FrListener
* refactor FrProvider.multi direct use providers as param
* rename **break** regAutoDispose -> `autoDispose`
    * bug: can not import `autoDispose`, please use 0.6.0

## 0.4.1 2025-6-14
* fix AutoDispose can't add subs

## 0.4.0 2025-6-13
* feat FrView readOnlyGlobal
* feat FrViewFutureBuilder,FrFutureBuilder
* feat FrReadContext onlyGlobal can set null; mean global first

## 0.3.0 2025-6-12
* feat FlowR initValue can't be null 
* feat readGlobal show instance shortHash
* feat FrProvider onCreated
* fix supprot flutter 3.16.7
* rename FrViewModelProvider -> FrProvider; FrViewModelMultiProvider -> FrMultiProvider

## 0.2.0 2025-6-9
* feat FrView/FrStreamBuilder stream new type 'Stream<T> Function(VM vm)?'
* fix downgrade rxdart to ^0.27.7; support more flutter SDK versions

## 0.1.0 2025-6-8

* feat FlowR
* feat FlowR-MVVM
 - FrModel
 - FrView/FrStreamBuilder
 - FrViewModel

