part of 'home_page.dart';

class _HomePageView extends StatelessWidget {
  const _HomePageView();

  @override
  Widget build(BuildContext context) {
    return FrView<HomePageViewModel, HomePageModel>(
      builder: (context, snap, child) => HomePageScaffold(snap: snap),
    );
  }
}

class HomePageScaffold extends StatelessWidget {
  final FrSnap<HomePageViewModel, HomePageModel> snap;

  const HomePageScaffold({required this.snap, super.key});

  @override
  Widget build(BuildContext context) {
    final data = snap.data;
    final payload = data.bootstrapData;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FC),
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: <Color>[Color(0xFFFFFCFD), Color(0xFFF4F6FB)],
          ),
        ),
        child: SafeArea(
          bottom: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 720),
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(24, 18, 24, 32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const HomePageHeader(),
                    const SizedBox(height: 28),
                    HomePortfolioCard(
                      summary: payload?.summary,
                      loading: data.loading,
                      errorMessage: data.errorMessage,
                      onRetry: () => snap.vm.add(const HomePageRetried()),
                    ),
                    const SizedBox(height: 28),
                    HomeStocksSection(
                      recommendations:
                          payload?.recommendations ??
                          const <HomeStockRecommendationModel>[],
                      selectedTicker: data.selectedTicker,
                      onStockSelected: (symbol) =>
                          snap.vm.add(HomeStockSelected(symbol: symbol)),
                    ),
                    const SizedBox(height: 30),
                    HomeOpinionsSection(
                      opinions:
                          payload?.opinions ??
                          const <HomeOpinionArticleModel>[],
                      loading: data.loading,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomePageHeader extends StatelessWidget {
  const HomePageHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return const Text(
      'Home',
      style: TextStyle(
        fontSize: 38,
        fontWeight: FontWeight.w800,
        letterSpacing: -1.2,
        color: Color(0xFF0E1116),
      ),
    );
  }
}

class HomePortfolioCard extends StatelessWidget {
  final HomePortfolioSummaryModel? summary;
  final bool loading;
  final String? errorMessage;
  final VoidCallback onRetry;

  const HomePortfolioCard({
    required this.summary,
    required this.loading,
    required this.errorMessage,
    required this.onRetry,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    if (loading && summary == null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(28),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(28),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: <Color>[Color(0xFFFF6BA1), Color(0xFFFF545C)],
          ),
          boxShadow: const <BoxShadow>[
            BoxShadow(
              color: Color(0x33FF5E8D),
              blurRadius: 36,
              offset: Offset(0, 20),
            ),
          ],
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(
                strokeWidth: 2.4,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            ),
            SizedBox(width: 16),
            Expanded(
              child: Text(
                'Loading your portfolio...',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      );
    }

    if (errorMessage != null && summary == null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1F2940),
          borderRadius: BorderRadius.circular(28),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Home bootstrap failed',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              errorMessage!,
              style: const TextStyle(color: Color(0xFFD5DAE7), height: 1.45),
            ),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: onRetry,
              style: FilledButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: const Color(0xFF1F2940),
                padding: const EdgeInsets.symmetric(
                  horizontal: 18,
                  vertical: 12,
                ),
              ),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (summary == null) {
      return const SizedBox.shrink();
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(28, 26, 28, 26),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[Color(0xFFFF6BA1), Color(0xFFFF545C)],
        ),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x33FF5E8D),
            blurRadius: 40,
            spreadRadius: 2,
            offset: Offset(0, 22),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            summary!.headline,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 18),
          Wrap(
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 12,
            runSpacing: 8,
            children: [
              Text(
                summary!.totalAssetLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 42,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1.8,
                  height: 1,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: const Color(0x26FFFFFF),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.arrow_upward_rounded,
                      size: 14,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      summary!.changeRateLabel,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class HomeStocksSection extends StatelessWidget {
  final List<HomeStockRecommendationModel> recommendations;
  final String? selectedTicker;
  final ValueChanged<String> onStockSelected;

  const HomeStocksSection({
    required this.recommendations,
    required this.selectedTicker,
    required this.onStockSelected,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                "What's to Buy?",
                style: TextStyle(
                  fontSize: 30,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1,
                  color: Color(0xFF111318),
                ),
              ),
            ),
            TextButton(
              onPressed: () {},
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFFFF5A63),
                textStyle: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              child: const Text('See All →'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 196,
          child: recommendations.isEmpty
              ? const Center(
                  child: Text(
                    'No stock cards available.',
                    style: TextStyle(color: Color(0xFF6B7280)),
                  ),
                )
              : ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: recommendations.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(width: 18),
                  itemBuilder: (context, index) {
                    final stock = recommendations[index];
                    return SizedBox(
                      width: 150,
                      child: HomeStockRecommendationCard(
                        stock: stock,
                        selected: stock.symbol == selectedTicker,
                        onTap: () => onStockSelected(stock.symbol),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class HomeStockRecommendationCard extends StatelessWidget {
  final HomeStockRecommendationModel stock;
  final bool selected;
  final VoidCallback onTap;

  const HomeStockRecommendationCard({
    required this.stock,
    required this.selected,
    required this.onTap,
    super.key,
  });

  Color _hexColor(String hex) {
    final normalized = hex.replaceFirst('#', '');
    final value = int.parse(normalized, radix: 16);
    return Color(normalized.length == 6 ? (0xFF000000 | value) : value);
  }

  String _logoTextFor(String symbol) {
    switch (symbol) {
      case 'AAPL':
        return 'A';
      case 'MCD':
        return 'M';
      case 'FB':
        return 'f';
      default:
        return symbol.substring(0, 1).toUpperCase();
    }
  }

  @override
  Widget build(BuildContext context) {
    final start = _hexColor(stock.gradientStartHex);
    final end = _hexColor(stock.gradientEndHex);

    return AnimatedScale(
      duration: const Duration(milliseconds: 180),
      scale: selected ? 1 : 0.98,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(28),
          onTap: onTap,
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(28),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: <Color>[start, end],
              ),
              boxShadow: [
                BoxShadow(
                  color: end.withValues(alpha: selected ? 0.34 : 0.18),
                  blurRadius: selected ? 28 : 18,
                  offset: const Offset(0, 18),
                ),
              ],
              border: selected
                  ? Border.all(
                      color: Colors.white.withValues(alpha: 0.82),
                      width: 1.4,
                    )
                  : null,
            ),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      _logoTextFor(stock.symbol),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    stock.symbol,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    stock.displayPrice,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomeOpinionsSection extends StatelessWidget {
  final List<HomeOpinionArticleModel> opinions;
  final bool loading;

  const HomeOpinionsSection({
    required this.opinions,
    required this.loading,
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(24, 28, 24, 18),
      decoration: const BoxDecoration(
        color: Color(0xFF232C41),
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(32),
          topRight: Radius.circular(32),
          bottomLeft: Radius.circular(32),
          bottomRight: Radius.circular(32),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ShaderMask(
            shaderCallback: (bounds) => const LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: <Color>[Color(0xFFFF6BA1), Color(0xFFFF595D)],
            ).createShader(bounds),
            blendMode: BlendMode.srcIn,
            child: const Text(
              "Today's Opinion",
              style: TextStyle(
                fontSize: 27,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.8,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 18),
          if (loading && opinions.isEmpty)
            const Padding(
              padding: EdgeInsets.only(bottom: 18),
              child: LinearProgressIndicator(
                minHeight: 4,
                backgroundColor: Color(0xFF334155),
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFFF6BA1)),
              ),
            ),
          for (var index = 0; index < opinions.length; index++) ...[
            HomeOpinionTile(opinion: opinions[index]),
            if (index != opinions.length - 1)
              const Divider(color: Color(0xFF44506B), height: 18),
          ],
        ],
      ),
    );
  }
}

class HomeOpinionTile extends StatelessWidget {
  final HomeOpinionArticleModel opinion;

  const HomeOpinionTile({required this.opinion, super.key});

  String _avatarLabel(String headline) {
    final words = headline
        .split(RegExp(r'\s+'))
        .where((word) => word.isNotEmpty)
        .take(2)
        .map((word) => word.substring(0, 1).toUpperCase())
        .join();
    return words.isEmpty ? 'OP' : words;
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                opinion.headline,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  height: 1.3,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                opinion.summary,
                style: const TextStyle(
                  color: Color(0xFFBAC3D6),
                  fontSize: 15,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 16),
        Container(
          width: 52,
          height: 52,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: const <BoxShadow>[
              BoxShadow(
                color: Color(0x14000000),
                blurRadius: 16,
                offset: Offset(0, 6),
              ),
            ],
          ),
          alignment: Alignment.center,
          child: Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: <Color>[Color(0xFFFF8AB8), Color(0xFF8CC7FF)],
              ),
            ),
            alignment: Alignment.center,
            child: Text(
              _avatarLabel(opinion.headline),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.4,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
