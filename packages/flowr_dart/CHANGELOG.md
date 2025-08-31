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
