## 0.15.0 2025-7-16
* feat DistinctByX 
  stream.distinctBy()
* export rxdart::DebounceExtensions
  stream.debounce()
  stream.debounceTime()
* feat FrViewModel::logger has default

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
* fix LoggableMx log frame max index is len-1
* fix FrStreamBuilder ModelSnapshot can't set null data (when init);
* remove FrStreamBuilder.diFirst

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
* feat view.dart FrPageMx, provide `autoDispose` method

## 0.5.0 2025-6-16
* rename (break) regAutoDispose -> `autoDispose`
  * bug: can not import `autoDispose`, please use 0.6.0
* feat PageAutoDisposeMx
* feat FrListener
* refactor FrProvider.multi direct use providers as param

## 0.4.1 2025-6-14
* fix AutoDispose can't add subs

## 0.4.0 2025-6-13
* feat FrView readOnlyGlobal
* feat FrViewFutureBuilder,FrFutureBuilder
* feat FrReadContext onlyGlobal can set null; mean global first

## 0.3.0 2025-6-12
* feat FlowR initValue can't be null 
* rename FrViewModelProvider -> FrProvider; FrViewModelMultiProvider -> FrMultiProvider
* fix supprot flutter 3.16.7
* feat readGlobal show instance shortHash
* feat FrProvider onCreated

## 0.2.0 2025-6-9
* feat FrView/FrStreamBuilder stream new type 'Stream<T> Function(VM vm)?'
* fix downgrade rxdart to ^0.27.7; support more flutter SDK versions

## 0.1.0 2025-6-8

* feat FlowR
* feat FlowR-MVVM
 - FrModel
 - FrView/FrStreamBuilder
 - FrViewModel

