part of 'home_page.dart';

sealed class HomePageEvent {
  const HomePageEvent();
}

class HomePageStarted extends HomePageEvent {
  const HomePageStarted();
}

class HomePageRetried extends HomePageEvent {
  const HomePageRetried();
}

class HomeStockSelected extends HomePageEvent {
  final String symbol;

  const HomeStockSelected({required this.symbol});
}

class HomePageViewModel extends FrBlocViewModel<HomePageEvent, HomePageModel> {
  HomePageViewModel() : super(const HomePageModel()) {
    on<HomePageStarted>((event, emit) async {
      emit(state.copyWith(loading: true, errorMessage: null));
      try {
        await Future<void>.delayed(const Duration(milliseconds: 180));
        final payload = _buildMockBootstrapData();
        emit(
          state.copyWith(
            loading: false,
            bootstrapData: payload,
            selectedTicker:
                state.selectedTicker ??
                (payload.recommendations.isEmpty
                    ? null
                    : payload.recommendations.first.symbol),
          ),
        );
      } catch (error) {
        emit(state.copyWith(loading: false, errorMessage: error.toString()));
      }
    });
    on<HomePageRetried>((event, emit) {
      add(const HomePageStarted());
    });
    on<HomeStockSelected>((event, emit) {
      emit(state.copyWith(selectedTicker: event.symbol));
    });
  }

  HomeBootstrapDto _buildMockBootstrapData() {
    return const HomeBootstrapDto(
      summary: HomePortfolioSummaryDto(
        headline: 'Your total asset portfolio',
        totalAssetLabel: '\$ 2.240.559',
        changeRateLabel: '+2%',
      ),
      recommendations: <HomeStockRecommendationDto>[
        HomeStockRecommendationDto(
          symbol: 'AAPL',
          displayPrice: '\$ 364.11',
          gradientStartHex: '#060606',
          gradientEndHex: '#666666',
        ),
        HomeStockRecommendationDto(
          symbol: 'MCD',
          displayPrice: '\$ 183.52',
          gradientStartHex: '#E50D0D',
          gradientEndHex: '#F26A00',
        ),
        HomeStockRecommendationDto(
          symbol: 'FB',
          displayPrice: '\$ 233.42',
          gradientStartHex: '#1B5FFF',
          gradientEndHex: '#57DFFF',
        ),
      ],
      opinions: <HomeOpinionArticleDto>[
        HomeOpinionArticleDto(
          id: 'stocks-2020',
          headline: 'Most Valuable Stocks 2020',
          summary:
              "This is how you set your foot for 2020 stock market recession. What's next...",
        ),
        HomeOpinionArticleDto(
          id: 'blue-chip',
          headline: 'How To Pick for a Blue Chip',
          summary:
              "What do you like to see? It's a very different market from 2018. The way...",
        ),
        HomeOpinionArticleDto(
          id: 'nasdaq',
          headline: 'Welcome to New NASDAQ',
          summary:
              'When we talk about the wall street, what looks good might be different',
        ),
      ],
    );
  }
}
