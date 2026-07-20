# bloc_concurrency

Use this reference for asynchronous `FlowB` or `FrBlocViewModel` event
handlers when overlapping events need an explicit policy.

## Decide Before Adding

Bloc processes events concurrently by default. Keep the default when handlers
are synchronous or overlapping work is independent and race-safe. Introduce
`bloc_concurrency` when same-type events can overlap and at least one of these
is true:

- completion order can emit stale state;
- duplicate requests or writes are unsafe or wasteful;
- every event must run in arrival order;
- rapid repeat events should keep only the first or latest in-flight work.

Add `bloc_concurrency` as a direct dependency of the package that imports it,
using the repository's configured Dart or Flutter package manager. Import its
public entry point:

```dart
import 'package:bloc_concurrency/bloc_concurrency.dart';
```

Do not add the package merely because a class extends `FlowB` or
`FrBlocViewModel`. Do not specify `concurrent()` just to reproduce Bloc's
default behavior.

## Select A Transformer

| Transformer | Choose when | Tradeoff |
| --- | --- | --- |
| `sequential()` | Every event must complete once, in arrival order; use for ordered writes or read-modify-write work. | Later events wait in an unbounded queue. |
| `droppable()` | Keep the active handler and ignore repeats, such as duplicate submit or load-more events. | Events received while busy are permanently discarded. |
| `restartable()` | The newest asynchronous request supersedes older work, such as search, filter, or refresh. | Earlier handler results are ignored; underlying external side effects may still occur. |
| `concurrent()` | Work is independent and overlap-safe. | Completion and emission order can differ from event arrival order; this is already the default. |

`restartable()` is for asynchronous handlers. It is not debounce: every new
event starts immediately. If the requirement is to wait for a quiet period,
use a purpose-built debounce transformer instead of describing
`restartable()` as debounce.

## Apply Per Handler

Pass the transformer to the inherited Bloc `on<E>` API:

```dart
class SearchBloc extends FlowB<SearchEvent, SearchState> {
  SearchBloc(this.api) : super(const SearchState()) {
    on<SearchRequested>(_onSearch, transformer: restartable());
    on<ResultSaved>(_onSave, transformer: sequential());
  }

  final SearchApi api;

  Future<void> _onSearch(
    SearchRequested event,
    Emitter<SearchState> emit,
  ) async {
    final results = await api.search(event.query);
    emit(state.copyWith(results: results));
  }

  Future<void> _onSave(ResultSaved event, Emitter<SearchState> emit) async {
    await api.save(event.result);
  }
}
```

The same pattern applies to `FrBlocViewModel<E, M>`.

Transformers coordinate only events handled by the same `on<E>` registration.
Separate subtype registrations have independent event buckets, so a
transformer on one does not serialize or cancel another. When different event
types must share one ordering or cancellation policy, register an appropriate
common event type with one handler or move the shared operation behind an
explicit coordinator.

Do not assume cancellation rolls back an HTTP request, file write, or other
external side effect. For `restartable()`, make superseded work harmless when
possible and avoid it for non-idempotent operations that must finish exactly
once.

## Verify Behavior

Write focused tests that add events without awaiting between them and control
handler completion. Assert the policy, not only the final happy-path state:

- `sequential()`: no overlap and arrival-order completion;
- `droppable()`: repeats during active work never run;
- `restartable()`: only the latest handler may affect emitted state;
- `concurrent()`: out-of-order completion remains safe.
