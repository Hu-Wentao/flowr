# fr_vm_communication

Use this reference when a task coordinates multiple `FrViewModel` or
`FrBlocViewModel` instances in one page, across parent/child pages, or with
app-wide state such as theme, locale, env, or user.

## API

- Register sibling view models with `FrProvider.multi(...)`.
- Use `context.read<T>(onlyProvider: true)` when the current subtree instance
  matters more than DI fallback.
- Use `FrProvider.value(...)` to reuse an existing view model instance in a
  pushed route, dialog, or nested subtree.
- Use `FrProvider(..., onCreated: ...)` or constructor injection to hand one
  view model into another at creation time.
- VM-to-VM subscriptions should listen to `otherVm.stream` and register the
  subscription with `autoDispose(...)`.
- Public callers of `FrBlocViewModel` should dispatch `add(event)`.
- `Navigator.pop(result)` is the default one-shot child-to-parent return
  channel.
- `FrUnionViewModel` is the small global typed-state shortcut, not the default
  architecture for large feature domains.

## Patterns

### Theme VM + arbitrary VM in one UI

Prefer UI composition when only the widget layer needs both pieces of data.
Let the theme VM drive `ThemeData`, then read theme extensions and the feature
VM state in the same widget.

```dart
FrProvider.multi(
  [
    FrProvider((context) => AppThemeViewModel()),
    FrProvider((context) => HomeViewModel()),
  ],
  child: FrView<AppThemeViewModel, AppThemeModel>(
    builder: (context, themeState, _) => Theme(
      data: ThemeData(extensions: themeState.data.extensions),
      child: FrView<HomeViewModel, HomeModel>(
        builder: (context, homeState, _) {
          final pageTheme = context.ofThm<HomePageTheme>();
          return Text('${pageTheme.title} / ${homeState.data.banner}');
        },
      ),
    ),
  ),
);
```

### Child page returns a result to the parent page

Prefer this for one-shot actions such as "save and refresh home".

```dart
final result = await Navigator.of(context).push<EditorResult>(
  MaterialPageRoute(
    builder: (_) => FrProvider(
      (context) => EditorViewModel(),
      child: const EditorPage(),
    ),
  ),
);

if (context.mounted && result != null) {
  context.read<HomeViewModel>(onlyProvider: true).add(
    HomeEditorResultApplied(result),
  );
}
```

### Reuse the same parent VM in a child route

Use `FrProvider.value` when the child route must operate on the exact same
view model instance as the parent page.

```dart
final homeVm = context.read<HomeViewModel>(onlyProvider: true);

Navigator.of(context).push(
  MaterialPageRoute(
    builder: (_) => FrProvider<HomeViewModel>.value(
      value: homeVm,
      child: const ChildPage(),
    ),
  ),
);
```

### Inject one VM into another for live coordination

Use this only when business logic, not just UI, depends on another VM.

```dart
class ProfileViewModel extends FrBlocViewModel<ProfileEvent, ProfileModel> {
  final AppLocaleViewModel localeVm;

  ProfileViewModel({required this.localeVm}) : super(const ProfileModel()) {
    autoDispose(
      localeVm.stream.listen((locale) {
        add(ProfileLocaleChanged(locale));
      }),
    );
  }
}
```

If you create both VMs with providers, `onCreated` can wire them together:

```dart
class ProfileViewModel extends FrBlocViewModel<ProfileEvent, ProfileModel> {
  ProfileViewModel() : super(const ProfileModel());

  void bindLocale(AppLocaleViewModel localeVm) {
    autoDispose(
      localeVm.stream.listen((locale) {
        add(ProfileLocaleChanged(locale));
      }),
      tag: 'locale',
    );
  }
}

FrProvider(
  (context) => ProfileViewModel(),
  onCreated: (context, profileVm) {
    profileVm.bindLocale(context.read<AppLocaleViewModel>(onlyProvider: true));
  },
  child: const ProfilePage(),
);
```

## Rules

- Prefer UI composition over VM-to-VM dependencies when only the widget layer
  needs combined state.
- For `FrBlocViewModel`, keep external writes event-driven with `add(event)`.
- If one VM listens to another, read the current `value` synchronously first if
  the initial state matters; `stream` does not replay the current state.
- Keep VM dependencies one-way. Avoid two VMs subscribing to each other.
- Use route results for one-shot child actions; use shared instances only for
  live coordination that must happen before the child route closes.
- If the same VM type appears multiple times in one subtree, scope each
  provider close to its consumer instead of reading by ambiguous ancestry.
- Reach for `FrUnionViewModel` only when the state set is small, typed, and
  intentionally global.
