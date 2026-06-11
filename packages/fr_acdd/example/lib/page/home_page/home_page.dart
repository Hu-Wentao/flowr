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
/// - [HomePageStarted]: bootstrap the home page bff dto
/// - [HomePageRetried]: retry bootstrap after a transient failure
/// - [HomeStockSelected]: update the locally selected stock card
/// ViewModels:
/// - [HomePageViewModel]: primary home page view model
/// Models:
/// - [HomePageModel]: primary page state
/// - [HomePortfolioSummaryReq]: summary request dto
/// - [HomeStockRecommendationReq]: recommendations request dto
/// - [HomeOpinionArticleReq]: opinions request dto
/// - [HomeBootstrapDataModel]: root home bootstrap dto
/// - [HomePortfolioSummaryModel]: portfolio summary dto
/// - [HomeStockRecommendationModel]: recommendation stock dto
/// - [HomeOpinionArticleModel]: opinion article dto
/// API:
/// - GET `<BASE>/home-page/summary`
///   [HomePortfolioSummaryReq], [HomePortfolioSummaryModel]
/// - GET `<BASE>/home-page/recommendations`
///   [HomeStockRecommendationReq], [HomeStockRecommendationModel]
/// - GET `<BASE>/home-page/opinions`
///   [HomeOpinionArticleReq], [HomeOpinionArticleModel]
@FrAcddPage(mode: FrAcddMode.bffDto, namespace: 'home_page', version: 1)
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
    HomeBootstrapDataModel? bootstrapData,
    String? selectedTicker,
    String? errorMessage,
  }) = _HomePageModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomePortfolioSummaryReq with _$HomePortfolioSummaryReq {
  const HomePortfolioSummaryReq._();

  const factory HomePortfolioSummaryReq() = _HomePortfolioSummaryReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationReq with _$HomeStockRecommendationReq {
  const HomeStockRecommendationReq._();

  const factory HomeStockRecommendationReq({
    @FrAcddField(tag: 1) @Default('home') String slot,
    @FrAcddField(tag: 2) @Default(3) int limit,
  }) = _HomeStockRecommendationReq;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeOpinionArticleReq with _$HomeOpinionArticleReq {
  const HomeOpinionArticleReq._();

  const factory HomeOpinionArticleReq({
    @FrAcddField(tag: 1) @Default('stocks') String topic,
    @FrAcddField(tag: 2) @Default(3) int limit,
  }) = _HomeOpinionArticleReq;
}

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Home screen bootstrap payload.',
)
@FrAcddFreezed
class HomeBootstrapDataModel with _$HomeBootstrapDataModel {
  const HomeBootstrapDataModel._();

  const factory HomeBootstrapDataModel({
    @FrAcddField(tag: 1) required HomePortfolioSummaryModel summary,
    @FrAcddField(tag: 2)
    @Default(<HomeStockRecommendationModel>[])
    List<HomeStockRecommendationModel> recommendations,
    @FrAcddField(tag: 3)
    @Default(<HomeOpinionArticleModel>[])
    List<HomeOpinionArticleModel> opinions,
  }) = _HomeBootstrapDataModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomePortfolioSummaryModel with _$HomePortfolioSummaryModel {
  const HomePortfolioSummaryModel._();

  const factory HomePortfolioSummaryModel({
    @FrAcddField(tag: 1) required String headline,
    @FrAcddField(tag: 2) required String totalAssetLabel,
    @FrAcddField(tag: 3) required String changeRateLabel,
  }) = _HomePortfolioSummaryModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationModel with _$HomeStockRecommendationModel {
  const HomeStockRecommendationModel._();

  const factory HomeStockRecommendationModel({
    @FrAcddField(tag: 1) required String symbol,
    @FrAcddField(tag: 2) required String displayPrice,
    @FrAcddField(tag: 3) required String gradientStartHex,
    @FrAcddField(tag: 4) required String gradientEndHex,
  }) = _HomeStockRecommendationModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeOpinionArticleModel with _$HomeOpinionArticleModel {
  const HomeOpinionArticleModel._();

  const factory HomeOpinionArticleModel({
    @FrAcddField(tag: 1) required String id,
    @FrAcddField(tag: 2) required String headline,
    @FrAcddField(tag: 3) required String summary,
  }) = _HomeOpinionArticleModel;
}
