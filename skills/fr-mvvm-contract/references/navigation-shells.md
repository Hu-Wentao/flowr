# Persistent Navigation Shells

Use this task before generating, repairing, or routing two or more destinations
that share a persistent bottom navigation region.

## Classify The Navigation Owner First

Treat a Figma Frame as `shell state + branch content`, not automatically as one
complete route-owned Scaffold. Group destinations into one navigation shell
when the evidence establishes all of these facts:

- the bottom destinations, order, and semantics are the same;
- only the active destination or destination-specific content changes;
- switching destinations must keep the navigation chrome mounted;
- each destination has its own route identity or branch state;
- product behavior, Figma component identity, or existing routing confirms the
  shared lifecycle.

Do not group Frames solely because their navigation bars look similar. Record
ambiguous membership as a decision gap before changing routes.

Classify every route in scope as one of:

- **shell branch root**: a primary destination selected by the persistent bar;
- **branch child**: a detail or flow route pushed inside one branch stack;
- **root fullscreen**: a route intentionally outside or above the shell;
- **root overlay**: a dialog or sheet that must cover persistent chrome;
- **branch overlay**: an overlay intentionally bounded to one branch.

## Ownership Contract

One shell owns exactly one outer `Scaffold`, persistent bottom navigation
instance, and persistent top-region host. A shared top-region host may render a
destination-specific title or action configuration; shared ownership does not
require identical visible content.

Each branch Page continues to own its route inputs and page-scoped Provider.
Its View owns branch content only. It must not create another outer `Scaffold`,
bottom navigation, or persistent top-region host.

Keep the bottom-navigation Widget presentation-only:

- accept the selected destination and callbacks as inputs;
- never import branch Page adapters;
- never call `.go`, `.push`, `.replace`, or raw router navigation;
- never own a Provider or branch ViewModel.

The shell maps navigation selections to branch switching or an explicitly
declared root action. Branch-internal navigation continues to use typed Page
helpers.

## Root actions and guarded entry

Separate root actions by preflight responsibility:

- With no permission, validation, API, business-policy, or asynchronous
  preflight, the Shell View callback may invoke the known typed Page directly.
- With any such preflight, the bottom-navigation tap expresses intent only. It
  calls a Shell callback that dispatches a Shell-owned component Event. The
  Shell-owned component ViewModel injects the gateway, applies guard and
  concurrency policy, publishes approved/blocked state, and sets a nullable
  semantic navigation signal only for approval. A Shell View
  `FrListener`/`FrConsumer` performs the typed Page navigation.

Keep the guarded-entry Provider/ViewModel lifecycle at the Shell owner so it
survives branch changes and remains available when the root action is tapped
again. Do not place the gate in the passive bottom-navigation Widget, any branch
ViewModel, or the target Page ViewModel. The target Page owns only its lifecycle
after navigation succeeds.

Default guarded root actions to `ignore-while-active`. Pending clears the
navigation signal. Blocked and exception exits reset the active guard, expose
an observable outcome, and never set the signal. After completion, a later tap
may run a fresh preflight and re-enter the root fullscreen flow.

## Router Selection

Use `StatefulShellRoute.indexedStack` by default when bottom destinations must
switch without a full-page transition and preserve independent navigation and
widget state. Call `StatefulNavigationShell.goBranch(index)` from the shell.

Use `ShellRoute` only when the product explicitly does not require independent
branch stacks or retained branch state. A `NoTransitionPage` or zero-duration
transition is not a substitute for a persistent shell: it can hide animation
while still destroying and recreating navigation chrome.

Declare reselect behavior explicitly. Use no-op/retain by default; reset a
branch to its root only when product behavior requires it.

## Branch Reactivation And Query Freshness

Preserving a branch's Widget and Provider state does not keep its query data
fresh. For every shell branch whose component contract declares a query API:

- observe the branch's actual inactive-to-active transition;
- dispatch its established query load/refresh Event into the retained
  page-owned ViewModel when it becomes active again;
- let initial Provider creation dispatch the Startup Event exactly once, and do
  not issue a second request merely because the branch first builds active;
- do not refresh for an ordinary rebuild or a selected-branch reselect unless
  product behavior explicitly requires that policy;
- preserve current data while refreshing when the component contract declares
  stale-while-refresh behavior; and
- make overlapping refreshes latest-result-safe through the project's FlowR
  concurrency policy or an equivalent stale-response guard.

The shell may expose its active branch through an inherited/listenable signal,
or another established lifecycle mechanism may provide equivalent evidence.
Do not recreate the branch Provider or clear retained UI state to obtain a fresh
query result. A local-only or command-only branch does not acquire a query
refresh merely because it belongs to the shell.

## Overlay And Deep-Link Policy

Keep public route locations stable during a shell migration. A deep link to a
branch root or branch child must select the corresponding branch.

Present fullscreen flows and overlays that must cover the bottom navigation on
the root navigator or root overlay. Do not let a branch ViewModel hide or
recreate the shell to simulate coverage.

## Deterministic Validation

Resolve `validate_navigation_shell` and run its declared command before and
after a shell change. The project profile declares shell membership and
project-specific route and test paths. The reusable navigation-shell validator proves structural ownership and
profile-declared runtime evidence. The guarded-entry owning component's normal
contract/final validator separately proves its Event, Model, guard,
concurrency, approved/blocked state writes, navigation signal, listener, and
ViewModel router boundary. Do not turn `validate_navigation_shell.py` into a
project-specific Dart control-flow scanner.

The reusable validator must prove:

- the router uses the declared persistent-shell strategy;
- the shell is the only owner of outer Scaffold, top host, and bottom slot;
- bottom navigation is passive and contains no branch Page navigation;
- branch Views are content-only;
- every declared branch route and Page exists;
- focused tests cover stable shell identity, one-pump branch switching, branch
  state retention, deep links, and overlay policy;
- guarded root-action coverage, when applicable, proves blocked and approved
  outcomes, repeat taps while active, root-fullscreen coverage above shell
  chrome, and re-entry after returning; and
- focused tests for every query-owning branch count one initial API load and
  exactly one additional request for each inactive-to-active reactivation,
  while proving that an ordinary rebuild does not duplicate the load.

Also run build generation, analyzer, focused Widget tests, and applicable
route/E2E tests. Do not use `pumpAndSettle()` alone as evidence that branch
switching has no transition; assert the target after one `pump()` and compare
the persistent navigation Element before and after the switch.
