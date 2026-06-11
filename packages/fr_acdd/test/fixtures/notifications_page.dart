import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:fr_acdd/fr_acdd.dart';

abstract class StatelessWidget {
  const StatelessWidget({this.key});

  final Object? key;
}

enum NotificationsPagePhase { initial }

enum NotificationsPriority { low, high }

/// Figma: https://www.figma.com/file/abc123/notifications
/// State Ownership:
/// - page-local loading phase and selected tab
/// Route: AppRouter.notifications
/// Models:
/// - [NotificationsPageModel]: page-local state
/// - [NotificationsBootstrapReq]: bootstrap request dto
/// - [NotificationsTabsReq]: tabs request dto
/// - [NotificationsCountsByTabReq]: counts request dto
/// - [NotificationsScreenDataModel]: notification screen payload
/// - [NotificationsTabDataModel]: tab payload dto
/// - [NotificationsTabSummaryModel]: tab summary dto
/// BFF-API:
/// - GET <BASE>/notifications-page/bootstrap
///   [NotificationsBootstrapReq], [NotificationsScreenDataModel]
/// - GET <BASE>/notifications-page/tabs
///   [NotificationsTabsReq], [NotificationsTabDataModel]
/// - GET <BASE>/notifications-page/counts-by-tab
///   [NotificationsCountsByTabReq], [NotificationsTabSummaryModel]
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'notifications_page', version: 2)
class NotificationsPage extends StatelessWidget {
  const NotificationsPage({super.key});
}

@Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
)
class NotificationsPageModel with _$NotificationsPageModel {
  const factory NotificationsPageModel({
    @Default(NotificationsPagePhase.initial) NotificationsPagePhase phase,
    @Default('') String searchKeyword,
  }) = _NotificationsPageModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsBootstrapReq with _$NotificationsBootstrapReq {
  const factory NotificationsBootstrapReq() = _NotificationsBootstrapReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabsReq with _$NotificationsTabsReq {
  const factory NotificationsTabsReq({
    @FrAcddField(tag: 1) @Default('all') String tabId,
  }) = _NotificationsTabsReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsCountsByTabReq with _$NotificationsCountsByTabReq {
  const factory NotificationsCountsByTabReq() = _NotificationsCountsByTabReq;
}

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Notification screen payload.',
)
@FrAcddFreezed
class NotificationsScreenDataModel with _$NotificationsScreenDataModel {
  const factory NotificationsScreenDataModel({
    @FrAcddField(tag: 1)
    @Default(<NotificationsTabDataModel>[])
    List<NotificationsTabDataModel> tabs,
    @FrAcddField(tag: 2) DateTime? updatedAt,
    @FrAcddField(tag: 3) Map<String, NotificationsTabSummaryModel>? countsByTab,
    @FrAcddField(tag: 4, include: false) String? ignoredInternalValue,
  }) = _NotificationsScreenDataModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabDataModel with _$NotificationsTabDataModel {
  const factory NotificationsTabDataModel({
    @FrAcddField(tag: 1) required String title,
    @FrAcddField(tag: 2) NotificationsTabSummaryModel? summary,
    @FrAcddField(tag: 3) NotificationsPriority? priority,
  }) = _NotificationsTabDataModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabSummaryModel with _$NotificationsTabSummaryModel {
  const factory NotificationsTabSummaryModel({
    @FrAcddField(tag: 1) required int unreadCount,
  }) = _NotificationsTabSummaryModel;
}
