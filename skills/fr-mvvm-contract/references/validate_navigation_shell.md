# Validate Persistent Navigation Shell

Use this task before and after changing routes or Views that share a persistent
bottom navigation region.

1. Read `references/navigation-shells.md`.
2. Read the resolved project profile and treat its shell membership, route
   locations, source paths, and required regression tokens as project facts.
3. Run the resolved `validate_navigation_shell` command before editing. A
   failing preflight is evidence of the current ownership defect.
4. Repair ownership rather than suppressing transitions:
   - create one stateful indexed-stack shell;
   - make branch Views content-only;
   - make bottom navigation passive;
   - let an unconditional root action navigate from the Shell View callback;
   - when a root action has preflight, give a Shell-owned component ViewModel
     the injected gateway, guard/concurrency policy, observable approved/blocked
     outcome, and nullable navigation signal; keep the gate out of bottom-nav,
     branch, and target Page ViewModels;
   - retain public URLs and Page-owned Provider lifecycles;
   - for each query-owning branch, dispatch its load/refresh Event on an actual
     inactive-to-active reactivation without duplicating its initial load; and
   - make overlapping refresh results latest-result-safe.
5. Keep validator responsibilities separate:
   - `validate_navigation_shell.py` proves shell/router/chrome ownership,
     passive navigation, declared routes, and profile-required test evidence;
   - the guarded-entry owning component contract/final validator proves its
     Event dispatch, Model fields, guard, concurrency, approved/blocked writes,
     nullable signal, exact View listener, and ViewModel router boundary.
   Do not add project-specific guarded-entry control-flow scanning to the shell
   validator.
6. Run the validator again, then run build generation, analyzer, focused Widget
   tests, and route/E2E tests. Project regression tokens must include API-call
   coverage for query branch reactivation, not only final rendered state. When
   a guarded root action exists, focused runtime coverage must prove blocked and
   approved outcomes, repeat taps while active, root-fullscreen coverage above
   shell chrome, and re-entry after returning.

The profile schema is `fr-mvvm-contract.navigation-shell.v1`. Project-specific
shell ids, destinations, paths, Widget names, and test tokens belong in
`.agents/skills-config/fr-mvvm-contract/`, not in the reusable skill.
