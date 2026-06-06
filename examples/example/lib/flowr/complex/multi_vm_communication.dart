import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';

class CommunicationTheme extends FrPageTheme<CommunicationTheme> {
  final Color accent;
  final Color panel;
  final String toneLabel;

  const CommunicationTheme({
    required this.accent,
    required this.panel,
    required this.toneLabel,
  });

  @override
  Map<String, dynamic> toJson() => {
        'accent': accent.toHexString,
        'panel': panel.toHexString,
        'toneLabel': toneLabel,
      };
}

class CommunicationThemeModel extends FrThemeModel {
  final String displayName;
  final CommunicationTheme palette;

  CommunicationThemeModel({
    required super.themeId,
    required this.displayName,
    required this.palette,
  }) : super(startAt: null, endAt: null, priority: 0);

  @override
  Map<String, dynamic> toJson() => {
        'themeId': themeId,
        'displayName': displayName,
        'palette': palette,
      };
}

final _sunriseTheme = CommunicationThemeModel(
  themeId: 'sunrise',
  displayName: 'Sunrise',
  palette: CommunicationTheme(
    accent: Color(0xFFD97706),
    panel: Color(0xFFFFF3E0),
    toneLabel: 'Warm launch tone',
  ),
);

final _oceanTheme = CommunicationThemeModel(
  themeId: 'ocean',
  displayName: 'Ocean',
  palette: CommunicationTheme(
    accent: Color(0xFF0F766E),
    panel: Color(0xFFE0F2F1),
    toneLabel: 'Calm sync tone',
  ),
);

class CommunicationThemeViewModel
    extends FrThemeViewModel<CommunicationThemeModel> {
  CommunicationThemeViewModel()
      : super(_sunriseTheme, all: [_sunriseTheme, _oceanTheme]);
}

class HomeModel {
  final int completedCount;
  final int liveSyncCount;
  final String bannerText;
  final String lastSource;
  final bool highlightBanner;

  const HomeModel({
    this.completedCount = 2,
    this.liveSyncCount = 0,
    this.bannerText = 'Waiting for a child page action.',
    this.lastSource = 'home',
    this.highlightBanner = false,
  });

  HomeModel copyWith({
    int? completedCount,
    int? liveSyncCount,
    String? bannerText,
    String? lastSource,
    bool? highlightBanner,
  }) =>
      HomeModel(
        completedCount: completedCount ?? this.completedCount,
        liveSyncCount: liveSyncCount ?? this.liveSyncCount,
        bannerText: bannerText ?? this.bannerText,
        lastSource: lastSource ?? this.lastSource,
        highlightBanner: highlightBanner ?? this.highlightBanner,
      );
}

sealed class HomeEvent {
  const HomeEvent();
}

class HomeEditorResultApplied extends HomeEvent {
  final TaskEditorResult result;

  const HomeEditorResultApplied(this.result);
}

class HomeLiveSyncReceived extends HomeEvent {
  final String source;

  const HomeLiveSyncReceived({required this.source});
}

class HomeBannerResetRequested extends HomeEvent {
  const HomeBannerResetRequested();
}

class HomeViewModel extends FrBlocViewModel<HomeEvent, HomeModel> {
  HomeViewModel() : super(const HomeModel()) {
    on<HomeEditorResultApplied>((event, emit) {
      emit(
        state.copyWith(
          completedCount:
              state.completedCount + (event.result.markComplete ? 1 : 0),
          bannerText: 'Child result: ${event.result.title}',
          lastSource: 'editor result',
          highlightBanner: event.result.highlightHome,
        ),
      );
    });

    on<HomeLiveSyncReceived>((event, emit) {
      emit(
        state.copyWith(
          liveSyncCount: state.liveSyncCount + 1,
          bannerText: 'Live update from ${event.source}',
          lastSource: event.source,
          highlightBanner: true,
        ),
      );
    });

    on<HomeBannerResetRequested>((event, emit) {
      emit(
        state.copyWith(
          bannerText: 'Waiting for a child page action.',
          lastSource: 'home reset',
          highlightBanner: false,
        ),
      );
    });
  }
}

class TaskEditorResult {
  final String title;
  final bool markComplete;
  final bool highlightHome;

  const TaskEditorResult({
    required this.title,
    required this.markComplete,
    required this.highlightHome,
  });
}

class TaskEditorModel {
  final String draftTitle;
  final bool markComplete;
  final bool highlightHome;

  const TaskEditorModel({
    this.draftTitle = 'Review release checklist',
    this.markComplete = true,
    this.highlightHome = true,
  });

  TaskEditorModel copyWith({
    String? draftTitle,
    bool? markComplete,
    bool? highlightHome,
  }) =>
      TaskEditorModel(
        draftTitle: draftTitle ?? this.draftTitle,
        markComplete: markComplete ?? this.markComplete,
        highlightHome: highlightHome ?? this.highlightHome,
      );
}

sealed class TaskEditorEvent {
  const TaskEditorEvent();
}

class TaskDraftChanged extends TaskEditorEvent {
  final String value;

  const TaskDraftChanged(this.value);
}

class TaskCompleteToggled extends TaskEditorEvent {
  const TaskCompleteToggled();
}

class TaskHighlightToggled extends TaskEditorEvent {
  const TaskHighlightToggled();
}

class TaskEditorViewModel
    extends FrBlocViewModel<TaskEditorEvent, TaskEditorModel> {
  TaskEditorViewModel() : super(const TaskEditorModel()) {
    on<TaskDraftChanged>(
      (event, emit) => emit(state.copyWith(draftTitle: event.value)),
    );
    on<TaskCompleteToggled>(
      (event, emit) => emit(state.copyWith(markComplete: !state.markComplete)),
    );
    on<TaskHighlightToggled>(
      (event, emit) =>
          emit(state.copyWith(highlightHome: !state.highlightHome)),
    );
  }

  TaskEditorResult buildResult() => TaskEditorResult(
        title: state.draftTitle.trim(),
        markComplete: state.markComplete,
        highlightHome: state.highlightHome,
      );
}

class SharedChildModel {
  final int sentCount;
  final String lastAction;

  const SharedChildModel({
    this.sentCount = 0,
    this.lastAction = 'No live sync yet.',
  });

  SharedChildModel copyWith({
    int? sentCount,
    String? lastAction,
  }) =>
      SharedChildModel(
        sentCount: sentCount ?? this.sentCount,
        lastAction: lastAction ?? this.lastAction,
      );
}

sealed class SharedChildEvent {
  const SharedChildEvent();
}

class SharedChildSyncPressed extends SharedChildEvent {
  const SharedChildSyncPressed();
}

class SharedChildViewModel
    extends FrBlocViewModel<SharedChildEvent, SharedChildModel> {
  final HomeViewModel homeVm;

  SharedChildViewModel({required this.homeVm})
      : super(const SharedChildModel()) {
    on<SharedChildSyncPressed>((event, emit) {
      final nextCount = state.sentCount + 1;
      homeVm.add(
        HomeLiveSyncReceived(source: 'shared child vm #$nextCount'),
      );
      emit(
        state.copyWith(
          sentCount: nextCount,
          lastAction: 'Forwarded sync #$nextCount to HomeViewModel.',
        ),
      );
    });
  }
}

class MultiVmCommunicationExample extends StatelessWidget {
  const MultiVmCommunicationExample({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider.multi(
      [
        FrProvider((context) => CommunicationThemeViewModel()),
        FrProvider((context) => HomeViewModel()),
      ],
      child: FrView<CommunicationThemeViewModel, CommunicationThemeModel>(
        builder: (context, themeState, _) {
          final palette = themeState.data.palette;
          return Theme(
            data: ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(seedColor: palette.accent),
              scaffoldBackgroundColor: palette.panel,
              extensions: themeState.data.extensions,
            ),
            child: const _MultiVmCommunicationPage(),
          );
        },
      ),
    );
  }
}

class _MultiVmCommunicationPage extends StatelessWidget {
  const _MultiVmCommunicationPage();

  Future<void> _openEditorWithResult(BuildContext context) async {
    final routeTheme = Theme.of(context);
    final result = await Navigator.of(context).push<TaskEditorResult>(
      MaterialPageRoute(
        builder: (_) => Theme(
          data: routeTheme,
          child: FrProvider(
            (context) => TaskEditorViewModel(),
            child: const _TaskEditorPage(),
          ),
        ),
      ),
    );
    if (!context.mounted || result == null) return;
    context.read<HomeViewModel>(onlyProvider: true).add(
          HomeEditorResultApplied(result),
        );
  }

  Future<void> _openSharedChildPage(BuildContext context) {
    final routeTheme = Theme.of(context);
    final homeVm = context.read<HomeViewModel>(onlyProvider: true);
    return Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => Theme(
          data: routeTheme,
          child: FrProvider<HomeViewModel>.value(
            value: homeVm,
            child: FrProvider(
              (context) => SharedChildViewModel(homeVm: homeVm),
              child: const _SharedHomeChildPage(),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final palette = context.ofThm<CommunicationTheme>();
    return Scaffold(
      appBar: AppBar(
        title: const Text('FrBlocViewModel Multi-VM Communication'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            color: palette.accent.withValues(alpha: 0.08),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Pattern 1: let the UI read ThemeVM-derived theme data and '
                'HomeViewModel state together.\n\n'
                'Pattern 2: let a child page return a result, then update '
                'HomeViewModel after await.\n\n'
                'Pattern 3: for live cross-page coordination, reuse the same '
                'HomeViewModel with FrProvider.value and inject it into the '
                'child page view model.',
              ),
            ),
          ),
          const SizedBox(height: 16),
          FrView<CommunicationThemeViewModel, CommunicationThemeModel>(
            builder: (context, themeState, _) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'ThemeVM',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text('Current theme: ${themeState.data.displayName}'),
                    Text('Theme tone: ${themeState.data.palette.toneLabel}'),
                    const SizedBox(height: 12),
                    FrThemeSwitchView<CommunicationThemeViewModel,
                        CommunicationThemeModel>(
                      buildAnchorTile: (context, theme) => Row(
                        children: [
                          Container(
                            width: 12,
                            height: 12,
                            decoration: BoxDecoration(
                              color: theme.palette.accent,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${theme.displayName} (${theme.themeId})',
                            style: const TextStyle(color: Colors.black87),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          FrView<HomeViewModel, HomeModel>(
            builder: (context, state, _) {
              final theme = context.ofThm<CommunicationTheme>();
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ThemeVM + HomeVM in one UI',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      _MetricRow(
                        label: 'Theme tone',
                        value: theme.toneLabel,
                        color: theme.accent,
                      ),
                      _MetricRow(
                        label: 'Completed count',
                        value: '${state.data.completedCount}',
                      ),
                      _MetricRow(
                        label: 'Live sync count',
                        value: '${state.data.liveSyncCount}',
                      ),
                      _MetricRow(
                        label: 'Last source',
                        value: state.data.lastSource,
                      ),
                      const SizedBox(height: 12),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: state.data.highlightBanner
                              ? theme.accent.withValues(alpha: 0.14)
                              : theme.panel.withValues(alpha: 0.60),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: state.data.highlightBanner
                                ? theme.accent
                                : theme.accent.withValues(alpha: 0.30),
                          ),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(state.data.bannerText),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(
                          onPressed: () => context
                              .read<HomeViewModel>(onlyProvider: true)
                              .add(const HomeBannerResetRequested()),
                          child: const Text('Reset banner'),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Child page -> HomeViewModel via route result',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'The child page owns TaskEditorViewModel. On save it pops a '
                    'TaskEditorResult, and the parent page applies that result '
                    'to HomeViewModel.',
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: () => _openEditorWithResult(context),
                    icon: const Icon(Icons.open_in_new),
                    label: const Text('Open editor page'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Child VM -> HomeViewModel live sync',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'This route reuses the current HomeViewModel with '
                    'FrProvider.value, then injects it into SharedChildViewModel '
                    'for direct live coordination.',
                  ),
                  const SizedBox(height: 12),
                  FilledButton.tonalIcon(
                    onPressed: () => _openSharedChildPage(context),
                    icon: const Icon(Icons.sync),
                    label: const Text('Open shared child page'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TaskEditorPage extends StatefulWidget {
  const _TaskEditorPage();

  @override
  State<_TaskEditorPage> createState() => _TaskEditorPageState();
}

class _TaskEditorPageState extends State<_TaskEditorPage> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    final vm = context.read<TaskEditorViewModel>(onlyProvider: true);
    _controller = TextEditingController(text: vm.value.draftTitle);
    _controller.addListener(() {
      vm.add(TaskDraftChanged(_controller.text));
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Child Page: Result Pattern')),
      body: FrView<TaskEditorViewModel, TaskEditorModel>(
        builder: (context, state, _) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'This page owns TaskEditorViewModel. Saving returns a '
              'TaskEditorResult to the parent page instead of touching '
              'HomeViewModel directly.',
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Draft title',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: state.data.markComplete,
              onChanged: (_) => state.vm.add(const TaskCompleteToggled()),
              title: const Text('Increment completed count on save'),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: state.data.highlightHome,
              onChanged: (_) => state.vm.add(const TaskHighlightToggled()),
              title: const Text('Highlight the home banner'),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: state.data.draftTitle.trim().isEmpty
                  ? null
                  : () => Navigator.of(context).pop(state.vm.buildResult()),
              icon: const Icon(Icons.check),
              label: const Text('Pop result to parent'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SharedHomeChildPage extends StatelessWidget {
  const _SharedHomeChildPage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Child Page: Shared HomeViewModel')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'This route reuses the parent HomeViewModel with FrProvider.value, '
            'so the child page and parent page observe the same instance.',
          ),
          const SizedBox(height: 16),
          FrView<HomeViewModel, HomeModel>(
            builder: (context, state, _) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Shared HomeViewModel snapshot',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text('Banner: ${state.data.bannerText}'),
                    Text('Live sync count: ${state.data.liveSyncCount}'),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          FrView<SharedChildViewModel, SharedChildModel>(
            builder: (context, state, _) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SharedChildViewModel',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text('Sent count: ${state.data.sentCount}'),
                    Text(state.data.lastAction),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: () => state.vm.add(
                        const SharedChildSyncPressed(),
                      ),
                      icon: const Icon(Icons.send),
                      label: const Text('Send live update to HomeViewModel'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const _MetricRow({
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Expanded(child: Text(label)),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
