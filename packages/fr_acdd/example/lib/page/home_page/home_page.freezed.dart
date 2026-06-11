// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'home_page.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
  'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models',
);

/// @nodoc
mixin _$HomePageModel {
  bool get loading => throw _privateConstructorUsedError;
  HomeBootstrapDataModel? get bootstrapData =>
      throw _privateConstructorUsedError;
  String? get selectedTicker => throw _privateConstructorUsedError;
  String? get errorMessage => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomePageModelCopyWith<HomePageModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomePageModelCopyWith<$Res> {
  factory $HomePageModelCopyWith(
    HomePageModel value,
    $Res Function(HomePageModel) then,
  ) = _$HomePageModelCopyWithImpl<$Res, HomePageModel>;
  @useResult
  $Res call({
    bool loading,
    HomeBootstrapDataModel? bootstrapData,
    String? selectedTicker,
    String? errorMessage,
  });

  $HomeBootstrapDataModelCopyWith<$Res>? get bootstrapData;
}

/// @nodoc
class _$HomePageModelCopyWithImpl<$Res, $Val extends HomePageModel>
    implements $HomePageModelCopyWith<$Res> {
  _$HomePageModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? loading = null,
    Object? bootstrapData = freezed,
    Object? selectedTicker = freezed,
    Object? errorMessage = freezed,
  }) {
    return _then(
      _value.copyWith(
            loading: null == loading
                ? _value.loading
                : loading // ignore: cast_nullable_to_non_nullable
                      as bool,
            bootstrapData: freezed == bootstrapData
                ? _value.bootstrapData
                : bootstrapData // ignore: cast_nullable_to_non_nullable
                      as HomeBootstrapDataModel?,
            selectedTicker: freezed == selectedTicker
                ? _value.selectedTicker
                : selectedTicker // ignore: cast_nullable_to_non_nullable
                      as String?,
            errorMessage: freezed == errorMessage
                ? _value.errorMessage
                : errorMessage // ignore: cast_nullable_to_non_nullable
                      as String?,
          )
          as $Val,
    );
  }

  @override
  @pragma('vm:prefer-inline')
  $HomeBootstrapDataModelCopyWith<$Res>? get bootstrapData {
    if (_value.bootstrapData == null) {
      return null;
    }

    return $HomeBootstrapDataModelCopyWith<$Res>(_value.bootstrapData!, (
      value,
    ) {
      return _then(_value.copyWith(bootstrapData: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$HomePageModelImplCopyWith<$Res>
    implements $HomePageModelCopyWith<$Res> {
  factory _$$HomePageModelImplCopyWith(
    _$HomePageModelImpl value,
    $Res Function(_$HomePageModelImpl) then,
  ) = __$$HomePageModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    bool loading,
    HomeBootstrapDataModel? bootstrapData,
    String? selectedTicker,
    String? errorMessage,
  });

  @override
  $HomeBootstrapDataModelCopyWith<$Res>? get bootstrapData;
}

/// @nodoc
class __$$HomePageModelImplCopyWithImpl<$Res>
    extends _$HomePageModelCopyWithImpl<$Res, _$HomePageModelImpl>
    implements _$$HomePageModelImplCopyWith<$Res> {
  __$$HomePageModelImplCopyWithImpl(
    _$HomePageModelImpl _value,
    $Res Function(_$HomePageModelImpl) _then,
  ) : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? loading = null,
    Object? bootstrapData = freezed,
    Object? selectedTicker = freezed,
    Object? errorMessage = freezed,
  }) {
    return _then(
      _$HomePageModelImpl(
        loading: null == loading
            ? _value.loading
            : loading // ignore: cast_nullable_to_non_nullable
                  as bool,
        bootstrapData: freezed == bootstrapData
            ? _value.bootstrapData
            : bootstrapData // ignore: cast_nullable_to_non_nullable
                  as HomeBootstrapDataModel?,
        selectedTicker: freezed == selectedTicker
            ? _value.selectedTicker
            : selectedTicker // ignore: cast_nullable_to_non_nullable
                  as String?,
        errorMessage: freezed == errorMessage
            ? _value.errorMessage
            : errorMessage // ignore: cast_nullable_to_non_nullable
                  as String?,
      ),
    );
  }
}

/// @nodoc

class _$HomePageModelImpl extends _HomePageModel {
  const _$HomePageModelImpl({
    this.loading = true,
    this.bootstrapData,
    this.selectedTicker,
    this.errorMessage,
  }) : super._();

  @override
  @JsonKey()
  final bool loading;
  @override
  final HomeBootstrapDataModel? bootstrapData;
  @override
  final String? selectedTicker;
  @override
  final String? errorMessage;

  @override
  String toString() {
    return 'HomePageModel(loading: $loading, bootstrapData: $bootstrapData, selectedTicker: $selectedTicker, errorMessage: $errorMessage)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomePageModelImpl &&
            (identical(other.loading, loading) || other.loading == loading) &&
            (identical(other.bootstrapData, bootstrapData) ||
                other.bootstrapData == bootstrapData) &&
            (identical(other.selectedTicker, selectedTicker) ||
                other.selectedTicker == selectedTicker) &&
            (identical(other.errorMessage, errorMessage) ||
                other.errorMessage == errorMessage));
  }

  @override
  int get hashCode => Object.hash(
    runtimeType,
    loading,
    bootstrapData,
    selectedTicker,
    errorMessage,
  );

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomePageModelImplCopyWith<_$HomePageModelImpl> get copyWith =>
      __$$HomePageModelImplCopyWithImpl<_$HomePageModelImpl>(this, _$identity);
}

abstract class _HomePageModel extends HomePageModel {
  const factory _HomePageModel({
    final bool loading,
    final HomeBootstrapDataModel? bootstrapData,
    final String? selectedTicker,
    final String? errorMessage,
  }) = _$HomePageModelImpl;
  const _HomePageModel._() : super._();

  @override
  bool get loading;
  @override
  HomeBootstrapDataModel? get bootstrapData;
  @override
  String? get selectedTicker;
  @override
  String? get errorMessage;
  @override
  @JsonKey(ignore: true)
  _$$HomePageModelImplCopyWith<_$HomePageModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeBootstrapDataModel {
  @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
  HomePortfolioSummaryModel get summary => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
  List<HomeStockRecommendationModel> get recommendations =>
      throw _privateConstructorUsedError;
  @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
  List<HomeOpinionArticleModel> get opinions =>
      throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeBootstrapDataModelCopyWith<HomeBootstrapDataModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeBootstrapDataModelCopyWith<$Res> {
  factory $HomeBootstrapDataModelCopyWith(
    HomeBootstrapDataModel value,
    $Res Function(HomeBootstrapDataModel) then,
  ) = _$HomeBootstrapDataModelCopyWithImpl<$Res, HomeBootstrapDataModel>;
  @useResult
  $Res call({
    @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
    HomePortfolioSummaryModel summary,
    @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
    List<HomeStockRecommendationModel> recommendations,
    @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
    List<HomeOpinionArticleModel> opinions,
  });

  $HomePortfolioSummaryModelCopyWith<$Res> get summary;
}

/// @nodoc
class _$HomeBootstrapDataModelCopyWithImpl<
  $Res,
  $Val extends HomeBootstrapDataModel
>
    implements $HomeBootstrapDataModelCopyWith<$Res> {
  _$HomeBootstrapDataModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? summary = null,
    Object? recommendations = null,
    Object? opinions = null,
  }) {
    return _then(
      _value.copyWith(
            summary: null == summary
                ? _value.summary
                : summary // ignore: cast_nullable_to_non_nullable
                      as HomePortfolioSummaryModel,
            recommendations: null == recommendations
                ? _value.recommendations
                : recommendations // ignore: cast_nullable_to_non_nullable
                      as List<HomeStockRecommendationModel>,
            opinions: null == opinions
                ? _value.opinions
                : opinions // ignore: cast_nullable_to_non_nullable
                      as List<HomeOpinionArticleModel>,
          )
          as $Val,
    );
  }

  @override
  @pragma('vm:prefer-inline')
  $HomePortfolioSummaryModelCopyWith<$Res> get summary {
    return $HomePortfolioSummaryModelCopyWith<$Res>(_value.summary, (value) {
      return _then(_value.copyWith(summary: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$HomeBootstrapDataModelImplCopyWith<$Res>
    implements $HomeBootstrapDataModelCopyWith<$Res> {
  factory _$$HomeBootstrapDataModelImplCopyWith(
    _$HomeBootstrapDataModelImpl value,
    $Res Function(_$HomeBootstrapDataModelImpl) then,
  ) = __$$HomeBootstrapDataModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
    HomePortfolioSummaryModel summary,
    @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
    List<HomeStockRecommendationModel> recommendations,
    @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
    List<HomeOpinionArticleModel> opinions,
  });

  @override
  $HomePortfolioSummaryModelCopyWith<$Res> get summary;
}

/// @nodoc
class __$$HomeBootstrapDataModelImplCopyWithImpl<$Res>
    extends
        _$HomeBootstrapDataModelCopyWithImpl<$Res, _$HomeBootstrapDataModelImpl>
    implements _$$HomeBootstrapDataModelImplCopyWith<$Res> {
  __$$HomeBootstrapDataModelImplCopyWithImpl(
    _$HomeBootstrapDataModelImpl _value,
    $Res Function(_$HomeBootstrapDataModelImpl) _then,
  ) : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? summary = null,
    Object? recommendations = null,
    Object? opinions = null,
  }) {
    return _then(
      _$HomeBootstrapDataModelImpl(
        summary: null == summary
            ? _value.summary
            : summary // ignore: cast_nullable_to_non_nullable
                  as HomePortfolioSummaryModel,
        recommendations: null == recommendations
            ? _value._recommendations
            : recommendations // ignore: cast_nullable_to_non_nullable
                  as List<HomeStockRecommendationModel>,
        opinions: null == opinions
            ? _value._opinions
            : opinions // ignore: cast_nullable_to_non_nullable
                  as List<HomeOpinionArticleModel>,
      ),
    );
  }
}

/// @nodoc

class _$HomeBootstrapDataModelImpl extends _HomeBootstrapDataModel {
  const _$HomeBootstrapDataModelImpl({
    @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
    required this.summary,
    @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
    final List<HomeStockRecommendationModel> recommendations =
        const <HomeStockRecommendationModel>[],
    @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
    final List<HomeOpinionArticleModel> opinions =
        const <HomeOpinionArticleModel>[],
  }) : _recommendations = recommendations,
       _opinions = opinions,
       super._();

  @override
  @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
  final HomePortfolioSummaryModel summary;
  final List<HomeStockRecommendationModel> _recommendations;
  @override
  @JsonKey()
  @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
  List<HomeStockRecommendationModel> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  final List<HomeOpinionArticleModel> _opinions;
  @override
  @JsonKey()
  @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
  List<HomeOpinionArticleModel> get opinions {
    if (_opinions is EqualUnmodifiableListView) return _opinions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_opinions);
  }

  @override
  String toString() {
    return 'HomeBootstrapDataModel(summary: $summary, recommendations: $recommendations, opinions: $opinions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeBootstrapDataModelImpl &&
            (identical(other.summary, summary) || other.summary == summary) &&
            const DeepCollectionEquality().equals(
              other._recommendations,
              _recommendations,
            ) &&
            const DeepCollectionEquality().equals(other._opinions, _opinions));
  }

  @override
  int get hashCode => Object.hash(
    runtimeType,
    summary,
    const DeepCollectionEquality().hash(_recommendations),
    const DeepCollectionEquality().hash(_opinions),
  );

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeBootstrapDataModelImplCopyWith<_$HomeBootstrapDataModelImpl>
  get copyWith =>
      __$$HomeBootstrapDataModelImplCopyWithImpl<_$HomeBootstrapDataModelImpl>(
        this,
        _$identity,
      );
}

abstract class _HomeBootstrapDataModel extends HomeBootstrapDataModel {
  const factory _HomeBootstrapDataModel({
    @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
    required final HomePortfolioSummaryModel summary,
    @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
    final List<HomeStockRecommendationModel> recommendations,
    @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
    final List<HomeOpinionArticleModel> opinions,
  }) = _$HomeBootstrapDataModelImpl;
  const _HomeBootstrapDataModel._() : super._();

  @override
  @FrAcddField(tag: 1, nestedRef: HomePortfolioSummaryModel)
  HomePortfolioSummaryModel get summary;
  @override
  @FrAcddField(tag: 2, nestedRef: HomeStockRecommendationModel)
  List<HomeStockRecommendationModel> get recommendations;
  @override
  @FrAcddField(tag: 3, nestedRef: HomeOpinionArticleModel)
  List<HomeOpinionArticleModel> get opinions;
  @override
  @JsonKey(ignore: true)
  _$$HomeBootstrapDataModelImplCopyWith<_$HomeBootstrapDataModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomePortfolioSummaryModel {
  @FrAcddField(tag: 1)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2, wireName: 'total_asset_label')
  String get totalAssetLabel => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3, wireName: 'change_rate_label')
  String get changeRateLabel => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomePortfolioSummaryModelCopyWith<HomePortfolioSummaryModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomePortfolioSummaryModelCopyWith<$Res> {
  factory $HomePortfolioSummaryModelCopyWith(
    HomePortfolioSummaryModel value,
    $Res Function(HomePortfolioSummaryModel) then,
  ) = _$HomePortfolioSummaryModelCopyWithImpl<$Res, HomePortfolioSummaryModel>;
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String headline,
    @FrAcddField(tag: 2, wireName: 'total_asset_label') String totalAssetLabel,
    @FrAcddField(tag: 3, wireName: 'change_rate_label') String changeRateLabel,
  });
}

/// @nodoc
class _$HomePortfolioSummaryModelCopyWithImpl<
  $Res,
  $Val extends HomePortfolioSummaryModel
>
    implements $HomePortfolioSummaryModelCopyWith<$Res> {
  _$HomePortfolioSummaryModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? headline = null,
    Object? totalAssetLabel = null,
    Object? changeRateLabel = null,
  }) {
    return _then(
      _value.copyWith(
            headline: null == headline
                ? _value.headline
                : headline // ignore: cast_nullable_to_non_nullable
                      as String,
            totalAssetLabel: null == totalAssetLabel
                ? _value.totalAssetLabel
                : totalAssetLabel // ignore: cast_nullable_to_non_nullable
                      as String,
            changeRateLabel: null == changeRateLabel
                ? _value.changeRateLabel
                : changeRateLabel // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$HomePortfolioSummaryModelImplCopyWith<$Res>
    implements $HomePortfolioSummaryModelCopyWith<$Res> {
  factory _$$HomePortfolioSummaryModelImplCopyWith(
    _$HomePortfolioSummaryModelImpl value,
    $Res Function(_$HomePortfolioSummaryModelImpl) then,
  ) = __$$HomePortfolioSummaryModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String headline,
    @FrAcddField(tag: 2, wireName: 'total_asset_label') String totalAssetLabel,
    @FrAcddField(tag: 3, wireName: 'change_rate_label') String changeRateLabel,
  });
}

/// @nodoc
class __$$HomePortfolioSummaryModelImplCopyWithImpl<$Res>
    extends
        _$HomePortfolioSummaryModelCopyWithImpl<
          $Res,
          _$HomePortfolioSummaryModelImpl
        >
    implements _$$HomePortfolioSummaryModelImplCopyWith<$Res> {
  __$$HomePortfolioSummaryModelImplCopyWithImpl(
    _$HomePortfolioSummaryModelImpl _value,
    $Res Function(_$HomePortfolioSummaryModelImpl) _then,
  ) : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? headline = null,
    Object? totalAssetLabel = null,
    Object? changeRateLabel = null,
  }) {
    return _then(
      _$HomePortfolioSummaryModelImpl(
        headline: null == headline
            ? _value.headline
            : headline // ignore: cast_nullable_to_non_nullable
                  as String,
        totalAssetLabel: null == totalAssetLabel
            ? _value.totalAssetLabel
            : totalAssetLabel // ignore: cast_nullable_to_non_nullable
                  as String,
        changeRateLabel: null == changeRateLabel
            ? _value.changeRateLabel
            : changeRateLabel // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

class _$HomePortfolioSummaryModelImpl extends _HomePortfolioSummaryModel {
  const _$HomePortfolioSummaryModelImpl({
    @FrAcddField(tag: 1) required this.headline,
    @FrAcddField(tag: 2, wireName: 'total_asset_label')
    required this.totalAssetLabel,
    @FrAcddField(tag: 3, wireName: 'change_rate_label')
    required this.changeRateLabel,
  }) : super._();

  @override
  @FrAcddField(tag: 1)
  final String headline;
  @override
  @FrAcddField(tag: 2, wireName: 'total_asset_label')
  final String totalAssetLabel;
  @override
  @FrAcddField(tag: 3, wireName: 'change_rate_label')
  final String changeRateLabel;

  @override
  String toString() {
    return 'HomePortfolioSummaryModel(headline: $headline, totalAssetLabel: $totalAssetLabel, changeRateLabel: $changeRateLabel)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomePortfolioSummaryModelImpl &&
            (identical(other.headline, headline) ||
                other.headline == headline) &&
            (identical(other.totalAssetLabel, totalAssetLabel) ||
                other.totalAssetLabel == totalAssetLabel) &&
            (identical(other.changeRateLabel, changeRateLabel) ||
                other.changeRateLabel == changeRateLabel));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, headline, totalAssetLabel, changeRateLabel);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomePortfolioSummaryModelImplCopyWith<_$HomePortfolioSummaryModelImpl>
  get copyWith =>
      __$$HomePortfolioSummaryModelImplCopyWithImpl<
        _$HomePortfolioSummaryModelImpl
      >(this, _$identity);
}

abstract class _HomePortfolioSummaryModel extends HomePortfolioSummaryModel {
  const factory _HomePortfolioSummaryModel({
    @FrAcddField(tag: 1) required final String headline,
    @FrAcddField(tag: 2, wireName: 'total_asset_label')
    required final String totalAssetLabel,
    @FrAcddField(tag: 3, wireName: 'change_rate_label')
    required final String changeRateLabel,
  }) = _$HomePortfolioSummaryModelImpl;
  const _HomePortfolioSummaryModel._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get headline;
  @override
  @FrAcddField(tag: 2, wireName: 'total_asset_label')
  String get totalAssetLabel;
  @override
  @FrAcddField(tag: 3, wireName: 'change_rate_label')
  String get changeRateLabel;
  @override
  @JsonKey(ignore: true)
  _$$HomePortfolioSummaryModelImplCopyWith<_$HomePortfolioSummaryModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeStockRecommendationModel {
  @FrAcddField(tag: 1)
  String get symbol => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2, wireName: 'display_price')
  String get displayPrice => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
  String get gradientStartHex => throw _privateConstructorUsedError;
  @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
  String get gradientEndHex => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeStockRecommendationModelCopyWith<HomeStockRecommendationModel>
  get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeStockRecommendationModelCopyWith<$Res> {
  factory $HomeStockRecommendationModelCopyWith(
    HomeStockRecommendationModel value,
    $Res Function(HomeStockRecommendationModel) then,
  ) =
      _$HomeStockRecommendationModelCopyWithImpl<
        $Res,
        HomeStockRecommendationModel
      >;
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String symbol,
    @FrAcddField(tag: 2, wireName: 'display_price') String displayPrice,
    @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
    String gradientStartHex,
    @FrAcddField(tag: 4, wireName: 'gradient_end_hex') String gradientEndHex,
  });
}

/// @nodoc
class _$HomeStockRecommendationModelCopyWithImpl<
  $Res,
  $Val extends HomeStockRecommendationModel
>
    implements $HomeStockRecommendationModelCopyWith<$Res> {
  _$HomeStockRecommendationModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? symbol = null,
    Object? displayPrice = null,
    Object? gradientStartHex = null,
    Object? gradientEndHex = null,
  }) {
    return _then(
      _value.copyWith(
            symbol: null == symbol
                ? _value.symbol
                : symbol // ignore: cast_nullable_to_non_nullable
                      as String,
            displayPrice: null == displayPrice
                ? _value.displayPrice
                : displayPrice // ignore: cast_nullable_to_non_nullable
                      as String,
            gradientStartHex: null == gradientStartHex
                ? _value.gradientStartHex
                : gradientStartHex // ignore: cast_nullable_to_non_nullable
                      as String,
            gradientEndHex: null == gradientEndHex
                ? _value.gradientEndHex
                : gradientEndHex // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$HomeStockRecommendationModelImplCopyWith<$Res>
    implements $HomeStockRecommendationModelCopyWith<$Res> {
  factory _$$HomeStockRecommendationModelImplCopyWith(
    _$HomeStockRecommendationModelImpl value,
    $Res Function(_$HomeStockRecommendationModelImpl) then,
  ) = __$$HomeStockRecommendationModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String symbol,
    @FrAcddField(tag: 2, wireName: 'display_price') String displayPrice,
    @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
    String gradientStartHex,
    @FrAcddField(tag: 4, wireName: 'gradient_end_hex') String gradientEndHex,
  });
}

/// @nodoc
class __$$HomeStockRecommendationModelImplCopyWithImpl<$Res>
    extends
        _$HomeStockRecommendationModelCopyWithImpl<
          $Res,
          _$HomeStockRecommendationModelImpl
        >
    implements _$$HomeStockRecommendationModelImplCopyWith<$Res> {
  __$$HomeStockRecommendationModelImplCopyWithImpl(
    _$HomeStockRecommendationModelImpl _value,
    $Res Function(_$HomeStockRecommendationModelImpl) _then,
  ) : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? symbol = null,
    Object? displayPrice = null,
    Object? gradientStartHex = null,
    Object? gradientEndHex = null,
  }) {
    return _then(
      _$HomeStockRecommendationModelImpl(
        symbol: null == symbol
            ? _value.symbol
            : symbol // ignore: cast_nullable_to_non_nullable
                  as String,
        displayPrice: null == displayPrice
            ? _value.displayPrice
            : displayPrice // ignore: cast_nullable_to_non_nullable
                  as String,
        gradientStartHex: null == gradientStartHex
            ? _value.gradientStartHex
            : gradientStartHex // ignore: cast_nullable_to_non_nullable
                  as String,
        gradientEndHex: null == gradientEndHex
            ? _value.gradientEndHex
            : gradientEndHex // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

class _$HomeStockRecommendationModelImpl extends _HomeStockRecommendationModel {
  const _$HomeStockRecommendationModelImpl({
    @FrAcddField(tag: 1) required this.symbol,
    @FrAcddField(tag: 2, wireName: 'display_price') required this.displayPrice,
    @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
    required this.gradientStartHex,
    @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
    required this.gradientEndHex,
  }) : super._();

  @override
  @FrAcddField(tag: 1)
  final String symbol;
  @override
  @FrAcddField(tag: 2, wireName: 'display_price')
  final String displayPrice;
  @override
  @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
  final String gradientStartHex;
  @override
  @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
  final String gradientEndHex;

  @override
  String toString() {
    return 'HomeStockRecommendationModel(symbol: $symbol, displayPrice: $displayPrice, gradientStartHex: $gradientStartHex, gradientEndHex: $gradientEndHex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeStockRecommendationModelImpl &&
            (identical(other.symbol, symbol) || other.symbol == symbol) &&
            (identical(other.displayPrice, displayPrice) ||
                other.displayPrice == displayPrice) &&
            (identical(other.gradientStartHex, gradientStartHex) ||
                other.gradientStartHex == gradientStartHex) &&
            (identical(other.gradientEndHex, gradientEndHex) ||
                other.gradientEndHex == gradientEndHex));
  }

  @override
  int get hashCode => Object.hash(
    runtimeType,
    symbol,
    displayPrice,
    gradientStartHex,
    gradientEndHex,
  );

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeStockRecommendationModelImplCopyWith<
    _$HomeStockRecommendationModelImpl
  >
  get copyWith =>
      __$$HomeStockRecommendationModelImplCopyWithImpl<
        _$HomeStockRecommendationModelImpl
      >(this, _$identity);
}

abstract class _HomeStockRecommendationModel
    extends HomeStockRecommendationModel {
  const factory _HomeStockRecommendationModel({
    @FrAcddField(tag: 1) required final String symbol,
    @FrAcddField(tag: 2, wireName: 'display_price')
    required final String displayPrice,
    @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
    required final String gradientStartHex,
    @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
    required final String gradientEndHex,
  }) = _$HomeStockRecommendationModelImpl;
  const _HomeStockRecommendationModel._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get symbol;
  @override
  @FrAcddField(tag: 2, wireName: 'display_price')
  String get displayPrice;
  @override
  @FrAcddField(tag: 3, wireName: 'gradient_start_hex')
  String get gradientStartHex;
  @override
  @FrAcddField(tag: 4, wireName: 'gradient_end_hex')
  String get gradientEndHex;
  @override
  @JsonKey(ignore: true)
  _$$HomeStockRecommendationModelImplCopyWith<
    _$HomeStockRecommendationModelImpl
  >
  get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeOpinionArticleModel {
  @FrAcddField(tag: 1)
  String get id => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get summary => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeOpinionArticleModelCopyWith<HomeOpinionArticleModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeOpinionArticleModelCopyWith<$Res> {
  factory $HomeOpinionArticleModelCopyWith(
    HomeOpinionArticleModel value,
    $Res Function(HomeOpinionArticleModel) then,
  ) = _$HomeOpinionArticleModelCopyWithImpl<$Res, HomeOpinionArticleModel>;
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String id,
    @FrAcddField(tag: 2) String headline,
    @FrAcddField(tag: 3) String summary,
  });
}

/// @nodoc
class _$HomeOpinionArticleModelCopyWithImpl<
  $Res,
  $Val extends HomeOpinionArticleModel
>
    implements $HomeOpinionArticleModelCopyWith<$Res> {
  _$HomeOpinionArticleModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? headline = null,
    Object? summary = null,
  }) {
    return _then(
      _value.copyWith(
            id: null == id
                ? _value.id
                : id // ignore: cast_nullable_to_non_nullable
                      as String,
            headline: null == headline
                ? _value.headline
                : headline // ignore: cast_nullable_to_non_nullable
                      as String,
            summary: null == summary
                ? _value.summary
                : summary // ignore: cast_nullable_to_non_nullable
                      as String,
          )
          as $Val,
    );
  }
}

/// @nodoc
abstract class _$$HomeOpinionArticleModelImplCopyWith<$Res>
    implements $HomeOpinionArticleModelCopyWith<$Res> {
  factory _$$HomeOpinionArticleModelImplCopyWith(
    _$HomeOpinionArticleModelImpl value,
    $Res Function(_$HomeOpinionArticleModelImpl) then,
  ) = __$$HomeOpinionArticleModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({
    @FrAcddField(tag: 1) String id,
    @FrAcddField(tag: 2) String headline,
    @FrAcddField(tag: 3) String summary,
  });
}

/// @nodoc
class __$$HomeOpinionArticleModelImplCopyWithImpl<$Res>
    extends
        _$HomeOpinionArticleModelCopyWithImpl<
          $Res,
          _$HomeOpinionArticleModelImpl
        >
    implements _$$HomeOpinionArticleModelImplCopyWith<$Res> {
  __$$HomeOpinionArticleModelImplCopyWithImpl(
    _$HomeOpinionArticleModelImpl _value,
    $Res Function(_$HomeOpinionArticleModelImpl) _then,
  ) : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? headline = null,
    Object? summary = null,
  }) {
    return _then(
      _$HomeOpinionArticleModelImpl(
        id: null == id
            ? _value.id
            : id // ignore: cast_nullable_to_non_nullable
                  as String,
        headline: null == headline
            ? _value.headline
            : headline // ignore: cast_nullable_to_non_nullable
                  as String,
        summary: null == summary
            ? _value.summary
            : summary // ignore: cast_nullable_to_non_nullable
                  as String,
      ),
    );
  }
}

/// @nodoc

class _$HomeOpinionArticleModelImpl extends _HomeOpinionArticleModel {
  const _$HomeOpinionArticleModelImpl({
    @FrAcddField(tag: 1) required this.id,
    @FrAcddField(tag: 2) required this.headline,
    @FrAcddField(tag: 3) required this.summary,
  }) : super._();

  @override
  @FrAcddField(tag: 1)
  final String id;
  @override
  @FrAcddField(tag: 2)
  final String headline;
  @override
  @FrAcddField(tag: 3)
  final String summary;

  @override
  String toString() {
    return 'HomeOpinionArticleModel(id: $id, headline: $headline, summary: $summary)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeOpinionArticleModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.headline, headline) ||
                other.headline == headline) &&
            (identical(other.summary, summary) || other.summary == summary));
  }

  @override
  int get hashCode => Object.hash(runtimeType, id, headline, summary);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeOpinionArticleModelImplCopyWith<_$HomeOpinionArticleModelImpl>
  get copyWith =>
      __$$HomeOpinionArticleModelImplCopyWithImpl<
        _$HomeOpinionArticleModelImpl
      >(this, _$identity);
}

abstract class _HomeOpinionArticleModel extends HomeOpinionArticleModel {
  const factory _HomeOpinionArticleModel({
    @FrAcddField(tag: 1) required final String id,
    @FrAcddField(tag: 2) required final String headline,
    @FrAcddField(tag: 3) required final String summary,
  }) = _$HomeOpinionArticleModelImpl;
  const _HomeOpinionArticleModel._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get id;
  @override
  @FrAcddField(tag: 2)
  String get headline;
  @override
  @FrAcddField(tag: 3)
  String get summary;
  @override
  @JsonKey(ignore: true)
  _$$HomeOpinionArticleModelImplCopyWith<_$HomeOpinionArticleModelImpl>
  get copyWith => throw _privateConstructorUsedError;
}
