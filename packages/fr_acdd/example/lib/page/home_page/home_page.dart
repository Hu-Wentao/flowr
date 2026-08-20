import 'package:flowr/flowr_mvvm.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter/material.dart';
import 'package:fr_acdd/fr_acdd.dart';

part 'home_page.freezed.dart';
part 'home_page.v.dart';
part 'home_page.vm.dart';

/// Figma: https://www.figma.com/design/8o2jFlD9xlVHQYmp2ddidb/Colorful-Stock-App---iOS-UI-Kit--Community-?node-id=14-11&t=BobLQ33X6rW4neR8-4 | Community stock app homepage adapted into a FlowR contract-first example.
/// State Ownership:
/// - [HomePageViewModel]: owns bootstrap trigger, retry flow, and ticker selection.
/// - [HomePageModel]: stores current BFF payload snapshot, loading flag, error text, and selectedTicker.
/// Route: MaterialApp.home
/// Reused Widgets: none
/// Widget Tree:
/// [HomePageScaffold]
/// |- [HomePageHeader]
/// |- [HomePortfolioCard]
/// |- [HomeStocksSection]
/// |  '- [HomeStockRecommendationCard]
/// '- [HomeOpinionsSection]
/// '- [HomeOpinionTile]
/// Theme: none
/// Events: [HomePageEvent]
/// - [HomePageStarted]: bootstrap the home page bff payload
/// - [HomePageRetried]: retry bootstrap after a transient failure
/// - [HomeStockSelected]: update the locally selected stock card
/// ViewModels:
/// - [HomePageViewModel]: primary home page view model
/// Models:
/// - [HomePageModel]: primary page state
/// BFF-UI-API:
/// - GET `<BASE>/home-page/summary`
///   [HomePortfolioSummaryBffReq], [HomePortfolioSummaryBffRsp]
/// - GET `<BASE>/home-page/recommendations`
///   [HomeStockRecommendationBffReq], [HomeStockRecommendationBffRsp]
/// - GET `<BASE>/home-page/opinions`
///   [HomeOpinionArticleBffReq], [HomeOpinionArticleBffRsp]
@FrAcddPage(mode: FrAcddMode.bff, namespace: 'home_page', version: 1)
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (context) => HomePageViewModel(),
      onCreated: (context, vm) {
        vm.add(const HomePageStarted());
      },
      child: const _HomePageView(),
    );
  }
}

@Freezed(
  copyWith: true,
  equal: true,
  toStringOverride: true,
  fromJson: false,
  toJson: false,
)
class HomePageModel with _$HomePageModel {
  const HomePageModel._();

  const factory HomePageModel({
    @Default(true) bool loading,
    HomeBootstrapDto? bootstrapData,
    String? selectedTicker,
    String? errorMessage,
  }) = _HomePageModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomePortfolioSummaryBffReq with _$HomePortfolioSummaryBffReq {
  const HomePortfolioSummaryBffReq._();

  const factory HomePortfolioSummaryBffReq() = _HomePortfolioSummaryBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationBffReq with _$HomeStockRecommendationBffReq {
  const HomeStockRecommendationBffReq._();

  const factory HomeStockRecommendationBffReq({
    @FrAcddField(tag: 1) @Default('home') String slot,
    @FrAcddField(tag: 2) @Default(3) int limit,
  }) = _HomeStockRecommendationBffReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeOpinionArticleBffReq with _$HomeOpinionArticleBffReq {
  const HomeOpinionArticleBffReq._();

  const factory HomeOpinionArticleBffReq({
    @FrAcddField(tag: 1) @Default('stocks') String topic,
    @FrAcddField(tag: 2) @Default(3) int limit,
  }) = _HomeOpinionArticleBffReq;
}

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Home screen bootstrap payload.',
)
@FrAcddFreezed
class HomeBootstrapDto with _$HomeBootstrapDto {
  const HomeBootstrapDto._();

  const factory HomeBootstrapDto({
    @FrAcddField(tag: 1) required HomePortfolioSummaryDto summary,
    @FrAcddField(tag: 2)
    @Default(<HomeStockRecommendationDto>[])
    List<HomeStockRecommendationDto> recommendations,
    @FrAcddField(tag: 3)
    @Default(<HomeOpinionArticleDto>[])
    List<HomeOpinionArticleDto> opinions,
  }) = _HomeBootstrapDto;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomePortfolioSummaryBffRsp with _$HomePortfolioSummaryBffRsp {
  const HomePortfolioSummaryBffRsp._();

  const factory HomePortfolioSummaryBffRsp({
    @FrAcddField(tag: 1) required String headline,
    @FrAcddField(tag: 2) required String totalAssetLabel,
    @FrAcddField(tag: 3) required String changeRateLabel,
  }) = _HomePortfolioSummaryBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationBffRsp with _$HomeStockRecommendationBffRsp {
  const HomeStockRecommendationBffRsp._();

  const factory HomeStockRecommendationBffRsp({
    @FrAcddField(tag: 1) required String symbol,
    @FrAcddField(tag: 2) required String displayPrice,
    @FrAcddField(tag: 3) required String gradientStartHex,
    @FrAcddField(tag: 4) required String gradientEndHex,
  }) = _HomeStockRecommendationBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeOpinionArticleBffRsp with _$HomeOpinionArticleBffRsp {
  const HomeOpinionArticleBffRsp._();

  const factory HomeOpinionArticleBffRsp({
    @FrAcddField(tag: 1) required String id,
    @FrAcddField(tag: 2) required String headline,
    @FrAcddField(tag: 3) required String summary,
  }) = _HomeOpinionArticleBffRsp;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomePortfolioSummaryDto with _$HomePortfolioSummaryDto {
  const HomePortfolioSummaryDto._();

  const factory HomePortfolioSummaryDto({
    @FrAcddField(tag: 1) required String headline,
    @FrAcddField(tag: 2) required String totalAssetLabel,
    @FrAcddField(tag: 3) required String changeRateLabel,
  }) = _HomePortfolioSummaryDto;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationDto with _$HomeStockRecommendationDto {
  const HomeStockRecommendationDto._();

  const factory HomeStockRecommendationDto({
    @FrAcddField(tag: 1) required String symbol,
    @FrAcddField(tag: 2) required String displayPrice,
    @FrAcddField(tag: 3) required String gradientStartHex,
    @FrAcddField(tag: 4) required String gradientEndHex,
  }) = _HomeStockRecommendationDto;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeOpinionArticleDto with _$HomeOpinionArticleDto {
  const HomeOpinionArticleDto._();

  const factory HomeOpinionArticleDto({
    @FrAcddField(tag: 1) required String id,
    @FrAcddField(tag: 2) required String headline,
    @FrAcddField(tag: 3) required String summary,
  }) = _HomeOpinionArticleDto;
}
