import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:fr_acdd/fr_acdd.dart';

abstract class StatelessWidget {
  const StatelessWidget({this.key});

  final Object? key;
}

enum NotificationsPagePhase { initial }

enum NotificationsPriority { low, high }

/// Figma: https://www.figma.com/file/abc123/notifications
/// API: none
/// State Ownership:
/// - page-local loading phase and selected tab
/// Route: AppRouter.notifications
@FrAcddPage(
  mode: FrAcddMode.bffDto,
  namespace: 'notifications_page',
  version: 2,
)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}

@FrAcddDto(kind: FrAcddDtoKind.state)
@freezed
class NotificationsPageModel with _$NotificationsPageModel {
  const factory NotificationsPageModel({
    @Default(NotificationsPagePhase.initial) NotificationsPagePhase phase,
    @Default('') String searchKeyword,
  }) = _NotificationsPageModel;
}

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Notification screen payload.',
)
@freezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    @FrAcddField(tag: 1, nestedRef: NotificationsTabDataModel)
    @Default(<NotificationsTabDataModel>[])
    List<NotificationsTabDataModel> tabs,
    @FrAcddField(tag: 2, wireName: 'selected_tab') required String selectedTab,
    @FrAcddField(tag: 3, wireName: 'updated_at') DateTime? updatedAt,
    @FrAcddField(tag: 4, wireName: 'counts_by_tab')
    Map<String, NotificationsTabSummaryModel>? countsByTab,
    @FrAcddField(tag: 5, include: false) String? ignoredInternalValue,
  }) = _NotificationsScreenDataModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@freezed
class NotificationsTabDataModel with _$NotificationsTabDataModel {
  const factory NotificationsTabDataModel({
    @FrAcddField(tag: 1, wireName: 'tab_title') required String title,
    @FrAcddField(tag: 2) NotificationsTabSummaryModel? summary,
    @FrAcddField(tag: 3) NotificationsPriority? priority,
  }) = _NotificationsTabDataModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@freezed
class NotificationsTabSummaryModel with _$NotificationsTabSummaryModel {
  const factory NotificationsTabSummaryModel({
    @FrAcddField(tag: 1) required int unreadCount,
  }) = _NotificationsTabSummaryModel;
}
