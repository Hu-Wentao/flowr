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
/// BFF-API:
/// - GET <BASE>/notifications-page/bootstrap
///   [NotificationsBootstrapBffReq], [NotificationsBootstrapBffRsp]
/// - GET <BASE>/notifications-page/tabs
///   [NotificationsTabsBffReq], [NotificationsTabsBffRsp]
/// - GET <BASE>/notifications-page/counts-by-tab
///   [NotificationsCountsByTabBffReq], [NotificationsCountsByTabBffRsp]
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
class NotificationsBootstrapBffReq with _$NotificationsBootstrapBffReq {
  const factory NotificationsBootstrapBffReq() = _NotificationsBootstrapBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabsBffReq with _$NotificationsTabsBffReq {
  const factory NotificationsTabsBffReq({
    @FrAcddField(tag: 1) @Default('all') String tabId,
  }) = _NotificationsTabsBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsCountsByTabBffReq with _$NotificationsCountsByTabBffReq {
  const factory NotificationsCountsByTabBffReq() =
      _NotificationsCountsByTabBffReq;
}

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Notification screen payload.',
)
@FrAcddFreezed
class NotificationsBootstrapBffRsp with _$NotificationsBootstrapBffRsp {
  const factory NotificationsBootstrapBffRsp({
    @FrAcddField(tag: 1)
    @Default(<NotificationsTabDto>[])
    List<NotificationsTabDto> tabs,
    @FrAcddField(tag: 2) DateTime? updatedAt,
    @FrAcddField(tag: 3) Map<String, NotificationsTabSummaryDto>? countsByTab,
    @FrAcddField(tag: 4, include: false) String? ignoredInternalValue,
  }) = _NotificationsBootstrapBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabsBffRsp with _$NotificationsTabsBffRsp {
  const factory NotificationsTabsBffRsp({
    @FrAcddField(tag: 1) required String title,
    @FrAcddField(tag: 2) NotificationsTabSummaryDto? summary,
    @FrAcddField(tag: 3) NotificationsPriority? priority,
  }) = _NotificationsTabsBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsCountsByTabBffRsp with _$NotificationsCountsByTabBffRsp {
  const factory NotificationsCountsByTabBffRsp({
    @FrAcddField(tag: 1) required int unreadCount,
  }) = _NotificationsCountsByTabBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabDto with _$NotificationsTabDto {
  const factory NotificationsTabDto({
    @FrAcddField(tag: 1) required String title,
    @FrAcddField(tag: 2) NotificationsTabSummaryDto? summary,
    @FrAcddField(tag: 3) NotificationsPriority? priority,
  }) = _NotificationsTabDto;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class NotificationsTabSummaryDto with _$NotificationsTabSummaryDto {
  const factory NotificationsTabSummaryDto({
    @FrAcddField(tag: 1) required int unreadCount,
  }) = _NotificationsTabSummaryDto;
}
