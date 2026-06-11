import 'package:flowr/flowr_mvvm.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:flutter/material.dart';
import 'package:fr_acdd/fr_acdd.dart';

part 'home_page.freezed.dart';
part 'home_page.v.dart';
part 'home_page.vm.dart';

/// Figma: https://www.figma.com/design/8o2jFlD9xlVHQYmp2ddidb/Colorful-Stock-App---iOS-UI-Kit--Community-?node-id=14-11&t=BobLQ33X6rW4neR8-4 | Community stock app homepage adapted into a FlowR contract-first example.
/// API:
/// - GET /bff/home/bootstrap owns the page aggregation contract returned to Flutter.
/// - GET /portfolio/summary contributes the asset title, amount, and change badge branch.
/// - GET /market/recommendations?slot=home contributes the horizontal stock recommendation cards.
/// - GET /news/opinions?topic=stocks contributes the Today's Opinion article list.
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
/// - [HomeBootstrapDataModel]: root home bootstrap dto
/// - [HomePortfolioSummaryModel]: portfolio summary dto
/// - [HomeStockRecommendationModel]: recommendation stock dto
/// - [HomeOpinionArticleModel]: opinion article dto
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

@FrAcddDto(
  kind: FrAcddDtoKind.root,
  description: 'Home screen bootstrap payload.',
)
@FrAcddFreezed
class HomeBootstrapDataModel with _$HomeBootstrapDataModel {
  const HomeBootstrapDataModel._();

  const factory HomeBootstrapDataModel({
    @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
    required HomePortfolioSummaryModel summary,
    @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
    @Default(<HomeStockRecommendationModel>[])
    List<HomeStockRecommendationModel> recommendations,
    @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
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
    @FrAcddField(tag: 2, wireName: 'total_asset_label')
    required String totalAssetLabel,
    @FrAcddField(tag: 3, wireName: 'change_rate_label')
    required String changeRateLabel,
  }) = _HomePortfolioSummaryModel;
}

@FrAcddDto(kind: FrAcddDtoKind.nested)
@FrAcddFreezed
class HomeStockRecommendationModel with _$HomeStockRecommendationModel {
  const HomeStockRecommendationModel._();

  const factory HomeStockRecommendationModel({
    @FrAcddField(tag: 1) required String symbol,
    @FrAcddField(tag: 2, wireName: 'display_price')
    required String displayPrice,
    @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
    required String gradientStartHex,
    @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
    required String gradientEndHex,
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
