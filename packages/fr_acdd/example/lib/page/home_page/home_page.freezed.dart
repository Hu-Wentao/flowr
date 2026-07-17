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
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$HomePageModel {
  bool get loading => throw _privateConstructorUsedError;
  HomeBootstrapDto? get bootstrapData => throw _privateConstructorUsedError;
  String? get selectedTicker => throw _privateConstructorUsedError;
  String? get errorMessage => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomePageModelCopyWith<HomePageModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomePageModelCopyWith<$Res> {
  factory $HomePageModelCopyWith(
          HomePageModel value, $Res Function(HomePageModel) then) =
      _$HomePageModelCopyWithImpl<$Res, HomePageModel>;
  @useResult
  $Res call(
      {bool loading,
      HomeBootstrapDto? bootstrapData,
      String? selectedTicker,
      String? errorMessage});

  $HomeBootstrapDtoCopyWith<$Res>? get bootstrapData;
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
    return _then(_value.copyWith(
      loading: null == loading
          ? _value.loading
          : loading // ignore: cast_nullable_to_non_nullable
              as bool,
      bootstrapData: freezed == bootstrapData
          ? _value.bootstrapData
          : bootstrapData // ignore: cast_nullable_to_non_nullable
              as HomeBootstrapDto?,
      selectedTicker: freezed == selectedTicker
          ? _value.selectedTicker
          : selectedTicker // ignore: cast_nullable_to_non_nullable
              as String?,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $HomeBootstrapDtoCopyWith<$Res>? get bootstrapData {
    if (_value.bootstrapData == null) {
      return null;
    }

    return $HomeBootstrapDtoCopyWith<$Res>(_value.bootstrapData!, (value) {
      return _then(_value.copyWith(bootstrapData: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$HomePageModelImplCopyWith<$Res>
    implements $HomePageModelCopyWith<$Res> {
  factory _$$HomePageModelImplCopyWith(
          _$HomePageModelImpl value, $Res Function(_$HomePageModelImpl) then) =
      __$$HomePageModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool loading,
      HomeBootstrapDto? bootstrapData,
      String? selectedTicker,
      String? errorMessage});

  @override
  $HomeBootstrapDtoCopyWith<$Res>? get bootstrapData;
}

/// @nodoc
class __$$HomePageModelImplCopyWithImpl<$Res>
    extends _$HomePageModelCopyWithImpl<$Res, _$HomePageModelImpl>
    implements _$$HomePageModelImplCopyWith<$Res> {
  __$$HomePageModelImplCopyWithImpl(
      _$HomePageModelImpl _value, $Res Function(_$HomePageModelImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? loading = null,
    Object? bootstrapData = freezed,
    Object? selectedTicker = freezed,
    Object? errorMessage = freezed,
  }) {
    return _then(_$HomePageModelImpl(
      loading: null == loading
          ? _value.loading
          : loading // ignore: cast_nullable_to_non_nullable
              as bool,
      bootstrapData: freezed == bootstrapData
          ? _value.bootstrapData
          : bootstrapData // ignore: cast_nullable_to_non_nullable
              as HomeBootstrapDto?,
      selectedTicker: freezed == selectedTicker
          ? _value.selectedTicker
          : selectedTicker // ignore: cast_nullable_to_non_nullable
              as String?,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$HomePageModelImpl extends _HomePageModel {
  const _$HomePageModelImpl(
      {this.loading = true,
      this.bootstrapData,
      this.selectedTicker,
      this.errorMessage})
      : super._();

  @override
  @JsonKey()
  final bool loading;
  @override
  final HomeBootstrapDto? bootstrapData;
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
      runtimeType, loading, bootstrapData, selectedTicker, errorMessage);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomePageModelImplCopyWith<_$HomePageModelImpl> get copyWith =>
      __$$HomePageModelImplCopyWithImpl<_$HomePageModelImpl>(this, _$identity);
}

abstract class _HomePageModel extends HomePageModel {
  const factory _HomePageModel(
      {final bool loading,
      final HomeBootstrapDto? bootstrapData,
      final String? selectedTicker,
      final String? errorMessage}) = _$HomePageModelImpl;
  const _HomePageModel._() : super._();

  @override
  bool get loading;
  @override
  HomeBootstrapDto? get bootstrapData;
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
mixin _$HomePortfolioSummaryBffReq {}

/// @nodoc
abstract class $HomePortfolioSummaryBffReqCopyWith<$Res> {
  factory $HomePortfolioSummaryBffReqCopyWith(HomePortfolioSummaryBffReq value,
          $Res Function(HomePortfolioSummaryBffReq) then) =
      _$HomePortfolioSummaryBffReqCopyWithImpl<$Res,
          HomePortfolioSummaryBffReq>;
}

/// @nodoc
class _$HomePortfolioSummaryBffReqCopyWithImpl<$Res,
        $Val extends HomePortfolioSummaryBffReq>
    implements $HomePortfolioSummaryBffReqCopyWith<$Res> {
  _$HomePortfolioSummaryBffReqCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;
}

/// @nodoc
abstract class _$$HomePortfolioSummaryBffReqImplCopyWith<$Res> {
  factory _$$HomePortfolioSummaryBffReqImplCopyWith(
          _$HomePortfolioSummaryBffReqImpl value,
          $Res Function(_$HomePortfolioSummaryBffReqImpl) then) =
      __$$HomePortfolioSummaryBffReqImplCopyWithImpl<$Res>;
}

/// @nodoc
class __$$HomePortfolioSummaryBffReqImplCopyWithImpl<$Res>
    extends _$HomePortfolioSummaryBffReqCopyWithImpl<$Res,
        _$HomePortfolioSummaryBffReqImpl>
    implements _$$HomePortfolioSummaryBffReqImplCopyWith<$Res> {
  __$$HomePortfolioSummaryBffReqImplCopyWithImpl(
      _$HomePortfolioSummaryBffReqImpl _value,
      $Res Function(_$HomePortfolioSummaryBffReqImpl) _then)
      : super(_value, _then);
}

/// @nodoc

class _$HomePortfolioSummaryBffReqImpl extends _HomePortfolioSummaryBffReq {
  const _$HomePortfolioSummaryBffReqImpl() : super._();

  @override
  String toString() {
    return 'HomePortfolioSummaryBffReq()';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomePortfolioSummaryBffReqImpl);
  }

  @override
  int get hashCode => runtimeType.hashCode;
}

abstract class _HomePortfolioSummaryBffReq extends HomePortfolioSummaryBffReq {
  const factory _HomePortfolioSummaryBffReq() =
      _$HomePortfolioSummaryBffReqImpl;
  const _HomePortfolioSummaryBffReq._() : super._();
}

/// @nodoc
mixin _$HomeStockRecommendationBffReq {
  @FrAcddField(tag: 1)
  String get slot => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  int get limit => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeStockRecommendationBffReqCopyWith<HomeStockRecommendationBffReq>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeStockRecommendationBffReqCopyWith<$Res> {
  factory $HomeStockRecommendationBffReqCopyWith(
          HomeStockRecommendationBffReq value,
          $Res Function(HomeStockRecommendationBffReq) then) =
      _$HomeStockRecommendationBffReqCopyWithImpl<$Res,
          HomeStockRecommendationBffReq>;
  @useResult
  $Res call({@FrAcddField(tag: 1) String slot, @FrAcddField(tag: 2) int limit});
}

/// @nodoc
class _$HomeStockRecommendationBffReqCopyWithImpl<$Res,
        $Val extends HomeStockRecommendationBffReq>
    implements $HomeStockRecommendationBffReqCopyWith<$Res> {
  _$HomeStockRecommendationBffReqCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? slot = null,
    Object? limit = null,
  }) {
    return _then(_value.copyWith(
      slot: null == slot
          ? _value.slot
          : slot // ignore: cast_nullable_to_non_nullable
              as String,
      limit: null == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeStockRecommendationBffReqImplCopyWith<$Res>
    implements $HomeStockRecommendationBffReqCopyWith<$Res> {
  factory _$$HomeStockRecommendationBffReqImplCopyWith(
          _$HomeStockRecommendationBffReqImpl value,
          $Res Function(_$HomeStockRecommendationBffReqImpl) then) =
      __$$HomeStockRecommendationBffReqImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({@FrAcddField(tag: 1) String slot, @FrAcddField(tag: 2) int limit});
}

/// @nodoc
class __$$HomeStockRecommendationBffReqImplCopyWithImpl<$Res>
    extends _$HomeStockRecommendationBffReqCopyWithImpl<$Res,
        _$HomeStockRecommendationBffReqImpl>
    implements _$$HomeStockRecommendationBffReqImplCopyWith<$Res> {
  __$$HomeStockRecommendationBffReqImplCopyWithImpl(
      _$HomeStockRecommendationBffReqImpl _value,
      $Res Function(_$HomeStockRecommendationBffReqImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? slot = null,
    Object? limit = null,
  }) {
    return _then(_$HomeStockRecommendationBffReqImpl(
      slot: null == slot
          ? _value.slot
          : slot // ignore: cast_nullable_to_non_nullable
              as String,
      limit: null == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$HomeStockRecommendationBffReqImpl
    extends _HomeStockRecommendationBffReq {
  const _$HomeStockRecommendationBffReqImpl(
      {@FrAcddField(tag: 1) this.slot = 'home',
      @FrAcddField(tag: 2) this.limit = 3})
      : super._();

  @override
  @JsonKey()
  @FrAcddField(tag: 1)
  final String slot;
  @override
  @JsonKey()
  @FrAcddField(tag: 2)
  final int limit;

  @override
  String toString() {
    return 'HomeStockRecommendationBffReq(slot: $slot, limit: $limit)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeStockRecommendationBffReqImpl &&
            (identical(other.slot, slot) || other.slot == slot) &&
            (identical(other.limit, limit) || other.limit == limit));
  }

  @override
  int get hashCode => Object.hash(runtimeType, slot, limit);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeStockRecommendationBffReqImplCopyWith<
          _$HomeStockRecommendationBffReqImpl>
      get copyWith => __$$HomeStockRecommendationBffReqImplCopyWithImpl<
          _$HomeStockRecommendationBffReqImpl>(this, _$identity);
}

abstract class _HomeStockRecommendationBffReq
    extends HomeStockRecommendationBffReq {
  const factory _HomeStockRecommendationBffReq(
          {@FrAcddField(tag: 1) final String slot,
          @FrAcddField(tag: 2) final int limit}) =
      _$HomeStockRecommendationBffReqImpl;
  const _HomeStockRecommendationBffReq._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get slot;
  @override
  @FrAcddField(tag: 2)
  int get limit;
  @override
  @JsonKey(ignore: true)
  _$$HomeStockRecommendationBffReqImplCopyWith<
          _$HomeStockRecommendationBffReqImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeOpinionArticleBffReq {
  @FrAcddField(tag: 1)
  String get topic => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  int get limit => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeOpinionArticleBffReqCopyWith<HomeOpinionArticleBffReq> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeOpinionArticleBffReqCopyWith<$Res> {
  factory $HomeOpinionArticleBffReqCopyWith(HomeOpinionArticleBffReq value,
          $Res Function(HomeOpinionArticleBffReq) then) =
      _$HomeOpinionArticleBffReqCopyWithImpl<$Res, HomeOpinionArticleBffReq>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String topic, @FrAcddField(tag: 2) int limit});
}

/// @nodoc
class _$HomeOpinionArticleBffReqCopyWithImpl<$Res,
        $Val extends HomeOpinionArticleBffReq>
    implements $HomeOpinionArticleBffReqCopyWith<$Res> {
  _$HomeOpinionArticleBffReqCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? topic = null,
    Object? limit = null,
  }) {
    return _then(_value.copyWith(
      topic: null == topic
          ? _value.topic
          : topic // ignore: cast_nullable_to_non_nullable
              as String,
      limit: null == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeOpinionArticleBffReqImplCopyWith<$Res>
    implements $HomeOpinionArticleBffReqCopyWith<$Res> {
  factory _$$HomeOpinionArticleBffReqImplCopyWith(
          _$HomeOpinionArticleBffReqImpl value,
          $Res Function(_$HomeOpinionArticleBffReqImpl) then) =
      __$$HomeOpinionArticleBffReqImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String topic, @FrAcddField(tag: 2) int limit});
}

/// @nodoc
class __$$HomeOpinionArticleBffReqImplCopyWithImpl<$Res>
    extends _$HomeOpinionArticleBffReqCopyWithImpl<$Res,
        _$HomeOpinionArticleBffReqImpl>
    implements _$$HomeOpinionArticleBffReqImplCopyWith<$Res> {
  __$$HomeOpinionArticleBffReqImplCopyWithImpl(
      _$HomeOpinionArticleBffReqImpl _value,
      $Res Function(_$HomeOpinionArticleBffReqImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? topic = null,
    Object? limit = null,
  }) {
    return _then(_$HomeOpinionArticleBffReqImpl(
      topic: null == topic
          ? _value.topic
          : topic // ignore: cast_nullable_to_non_nullable
              as String,
      limit: null == limit
          ? _value.limit
          : limit // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc

class _$HomeOpinionArticleBffReqImpl extends _HomeOpinionArticleBffReq {
  const _$HomeOpinionArticleBffReqImpl(
      {@FrAcddField(tag: 1) this.topic = 'stocks',
      @FrAcddField(tag: 2) this.limit = 3})
      : super._();

  @override
  @JsonKey()
  @FrAcddField(tag: 1)
  final String topic;
  @override
  @JsonKey()
  @FrAcddField(tag: 2)
  final int limit;

  @override
  String toString() {
    return 'HomeOpinionArticleBffReq(topic: $topic, limit: $limit)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeOpinionArticleBffReqImpl &&
            (identical(other.topic, topic) || other.topic == topic) &&
            (identical(other.limit, limit) || other.limit == limit));
  }

  @override
  int get hashCode => Object.hash(runtimeType, topic, limit);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeOpinionArticleBffReqImplCopyWith<_$HomeOpinionArticleBffReqImpl>
      get copyWith => __$$HomeOpinionArticleBffReqImplCopyWithImpl<
          _$HomeOpinionArticleBffReqImpl>(this, _$identity);
}

abstract class _HomeOpinionArticleBffReq extends HomeOpinionArticleBffReq {
  const factory _HomeOpinionArticleBffReq(
      {@FrAcddField(tag: 1) final String topic,
      @FrAcddField(tag: 2) final int limit}) = _$HomeOpinionArticleBffReqImpl;
  const _HomeOpinionArticleBffReq._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get topic;
  @override
  @FrAcddField(tag: 2)
  int get limit;
  @override
  @JsonKey(ignore: true)
  _$$HomeOpinionArticleBffReqImplCopyWith<_$HomeOpinionArticleBffReqImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeBootstrapDto {
  @FrAcddField(tag: 1)
  HomePortfolioSummaryDto get summary => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  List<HomeStockRecommendationDto> get recommendations =>
      throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  List<HomeOpinionArticleDto> get opinions =>
      throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeBootstrapDtoCopyWith<HomeBootstrapDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeBootstrapDtoCopyWith<$Res> {
  factory $HomeBootstrapDtoCopyWith(
          HomeBootstrapDto value, $Res Function(HomeBootstrapDto) then) =
      _$HomeBootstrapDtoCopyWithImpl<$Res, HomeBootstrapDto>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) HomePortfolioSummaryDto summary,
      @FrAcddField(tag: 2) List<HomeStockRecommendationDto> recommendations,
      @FrAcddField(tag: 3) List<HomeOpinionArticleDto> opinions});

  $HomePortfolioSummaryDtoCopyWith<$Res> get summary;
}

/// @nodoc
class _$HomeBootstrapDtoCopyWithImpl<$Res, $Val extends HomeBootstrapDto>
    implements $HomeBootstrapDtoCopyWith<$Res> {
  _$HomeBootstrapDtoCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as HomePortfolioSummaryDto,
      recommendations: null == recommendations
          ? _value.recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<HomeStockRecommendationDto>,
      opinions: null == opinions
          ? _value.opinions
          : opinions // ignore: cast_nullable_to_non_nullable
              as List<HomeOpinionArticleDto>,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $HomePortfolioSummaryDtoCopyWith<$Res> get summary {
    return $HomePortfolioSummaryDtoCopyWith<$Res>(_value.summary, (value) {
      return _then(_value.copyWith(summary: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$HomeBootstrapDtoImplCopyWith<$Res>
    implements $HomeBootstrapDtoCopyWith<$Res> {
  factory _$$HomeBootstrapDtoImplCopyWith(_$HomeBootstrapDtoImpl value,
          $Res Function(_$HomeBootstrapDtoImpl) then) =
      __$$HomeBootstrapDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) HomePortfolioSummaryDto summary,
      @FrAcddField(tag: 2) List<HomeStockRecommendationDto> recommendations,
      @FrAcddField(tag: 3) List<HomeOpinionArticleDto> opinions});

  @override
  $HomePortfolioSummaryDtoCopyWith<$Res> get summary;
}

/// @nodoc
class __$$HomeBootstrapDtoImplCopyWithImpl<$Res>
    extends _$HomeBootstrapDtoCopyWithImpl<$Res, _$HomeBootstrapDtoImpl>
    implements _$$HomeBootstrapDtoImplCopyWith<$Res> {
  __$$HomeBootstrapDtoImplCopyWithImpl(_$HomeBootstrapDtoImpl _value,
      $Res Function(_$HomeBootstrapDtoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? summary = null,
    Object? recommendations = null,
    Object? opinions = null,
  }) {
    return _then(_$HomeBootstrapDtoImpl(
      summary: null == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as HomePortfolioSummaryDto,
      recommendations: null == recommendations
          ? _value._recommendations
          : recommendations // ignore: cast_nullable_to_non_nullable
              as List<HomeStockRecommendationDto>,
      opinions: null == opinions
          ? _value._opinions
          : opinions // ignore: cast_nullable_to_non_nullable
              as List<HomeOpinionArticleDto>,
    ));
  }
}

/// @nodoc

class _$HomeBootstrapDtoImpl extends _HomeBootstrapDto {
  const _$HomeBootstrapDtoImpl(
      {@FrAcddField(tag: 1) required this.summary,
      @FrAcddField(tag: 2)
      final List<HomeStockRecommendationDto> recommendations =
          const <HomeStockRecommendationDto>[],
      @FrAcddField(tag: 3) final List<HomeOpinionArticleDto> opinions =
          const <HomeOpinionArticleDto>[]})
      : _recommendations = recommendations,
        _opinions = opinions,
        super._();

  @override
  @FrAcddField(tag: 1)
  final HomePortfolioSummaryDto summary;
  final List<HomeStockRecommendationDto> _recommendations;
  @override
  @JsonKey()
  @FrAcddField(tag: 2)
  List<HomeStockRecommendationDto> get recommendations {
    if (_recommendations is EqualUnmodifiableListView) return _recommendations;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendations);
  }

  final List<HomeOpinionArticleDto> _opinions;
  @override
  @JsonKey()
  @FrAcddField(tag: 3)
  List<HomeOpinionArticleDto> get opinions {
    if (_opinions is EqualUnmodifiableListView) return _opinions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_opinions);
  }

  @override
  String toString() {
    return 'HomeBootstrapDto(summary: $summary, recommendations: $recommendations, opinions: $opinions)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeBootstrapDtoImpl &&
            (identical(other.summary, summary) || other.summary == summary) &&
            const DeepCollectionEquality()
                .equals(other._recommendations, _recommendations) &&
            const DeepCollectionEquality().equals(other._opinions, _opinions));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      summary,
      const DeepCollectionEquality().hash(_recommendations),
      const DeepCollectionEquality().hash(_opinions));

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeBootstrapDtoImplCopyWith<_$HomeBootstrapDtoImpl> get copyWith =>
      __$$HomeBootstrapDtoImplCopyWithImpl<_$HomeBootstrapDtoImpl>(
          this, _$identity);
}

abstract class _HomeBootstrapDto extends HomeBootstrapDto {
  const factory _HomeBootstrapDto(
          {@FrAcddField(tag: 1) required final HomePortfolioSummaryDto summary,
          @FrAcddField(tag: 2)
          final List<HomeStockRecommendationDto> recommendations,
          @FrAcddField(tag: 3) final List<HomeOpinionArticleDto> opinions}) =
      _$HomeBootstrapDtoImpl;
  const _HomeBootstrapDto._() : super._();

  @override
  @FrAcddField(tag: 1)
  HomePortfolioSummaryDto get summary;
  @override
  @FrAcddField(tag: 2)
  List<HomeStockRecommendationDto> get recommendations;
  @override
  @FrAcddField(tag: 3)
  List<HomeOpinionArticleDto> get opinions;
  @override
  @JsonKey(ignore: true)
  _$$HomeBootstrapDtoImplCopyWith<_$HomeBootstrapDtoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomePortfolioSummaryBffRsp {
  @FrAcddField(tag: 1)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get totalAssetLabel => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get changeRateLabel => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomePortfolioSummaryBffRspCopyWith<HomePortfolioSummaryBffRsp>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomePortfolioSummaryBffRspCopyWith<$Res> {
  factory $HomePortfolioSummaryBffRspCopyWith(HomePortfolioSummaryBffRsp value,
          $Res Function(HomePortfolioSummaryBffRsp) then) =
      _$HomePortfolioSummaryBffRspCopyWithImpl<$Res,
          HomePortfolioSummaryBffRsp>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String headline,
      @FrAcddField(tag: 2) String totalAssetLabel,
      @FrAcddField(tag: 3) String changeRateLabel});
}

/// @nodoc
class _$HomePortfolioSummaryBffRspCopyWithImpl<$Res,
        $Val extends HomePortfolioSummaryBffRsp>
    implements $HomePortfolioSummaryBffRspCopyWith<$Res> {
  _$HomePortfolioSummaryBffRspCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomePortfolioSummaryBffRspImplCopyWith<$Res>
    implements $HomePortfolioSummaryBffRspCopyWith<$Res> {
  factory _$$HomePortfolioSummaryBffRspImplCopyWith(
          _$HomePortfolioSummaryBffRspImpl value,
          $Res Function(_$HomePortfolioSummaryBffRspImpl) then) =
      __$$HomePortfolioSummaryBffRspImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String headline,
      @FrAcddField(tag: 2) String totalAssetLabel,
      @FrAcddField(tag: 3) String changeRateLabel});
}

/// @nodoc
class __$$HomePortfolioSummaryBffRspImplCopyWithImpl<$Res>
    extends _$HomePortfolioSummaryBffRspCopyWithImpl<$Res,
        _$HomePortfolioSummaryBffRspImpl>
    implements _$$HomePortfolioSummaryBffRspImplCopyWith<$Res> {
  __$$HomePortfolioSummaryBffRspImplCopyWithImpl(
      _$HomePortfolioSummaryBffRspImpl _value,
      $Res Function(_$HomePortfolioSummaryBffRspImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? headline = null,
    Object? totalAssetLabel = null,
    Object? changeRateLabel = null,
  }) {
    return _then(_$HomePortfolioSummaryBffRspImpl(
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
    ));
  }
}

/// @nodoc

class _$HomePortfolioSummaryBffRspImpl extends _HomePortfolioSummaryBffRsp {
  const _$HomePortfolioSummaryBffRspImpl(
      {@FrAcddField(tag: 1) required this.headline,
      @FrAcddField(tag: 2) required this.totalAssetLabel,
      @FrAcddField(tag: 3) required this.changeRateLabel})
      : super._();

  @override
  @FrAcddField(tag: 1)
  final String headline;
  @override
  @FrAcddField(tag: 2)
  final String totalAssetLabel;
  @override
  @FrAcddField(tag: 3)
  final String changeRateLabel;

  @override
  String toString() {
    return 'HomePortfolioSummaryBffRsp(headline: $headline, totalAssetLabel: $totalAssetLabel, changeRateLabel: $changeRateLabel)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomePortfolioSummaryBffRspImpl &&
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
  _$$HomePortfolioSummaryBffRspImplCopyWith<_$HomePortfolioSummaryBffRspImpl>
      get copyWith => __$$HomePortfolioSummaryBffRspImplCopyWithImpl<
          _$HomePortfolioSummaryBffRspImpl>(this, _$identity);
}

abstract class _HomePortfolioSummaryBffRsp extends HomePortfolioSummaryBffRsp {
  const factory _HomePortfolioSummaryBffRsp(
          {@FrAcddField(tag: 1) required final String headline,
          @FrAcddField(tag: 2) required final String totalAssetLabel,
          @FrAcddField(tag: 3) required final String changeRateLabel}) =
      _$HomePortfolioSummaryBffRspImpl;
  const _HomePortfolioSummaryBffRsp._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get headline;
  @override
  @FrAcddField(tag: 2)
  String get totalAssetLabel;
  @override
  @FrAcddField(tag: 3)
  String get changeRateLabel;
  @override
  @JsonKey(ignore: true)
  _$$HomePortfolioSummaryBffRspImplCopyWith<_$HomePortfolioSummaryBffRspImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeStockRecommendationBffRsp {
  @FrAcddField(tag: 1)
  String get symbol => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get displayPrice => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get gradientStartHex => throw _privateConstructorUsedError;
  @FrAcddField(tag: 4)
  String get gradientEndHex => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeStockRecommendationBffRspCopyWith<HomeStockRecommendationBffRsp>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeStockRecommendationBffRspCopyWith<$Res> {
  factory $HomeStockRecommendationBffRspCopyWith(
          HomeStockRecommendationBffRsp value,
          $Res Function(HomeStockRecommendationBffRsp) then) =
      _$HomeStockRecommendationBffRspCopyWithImpl<$Res,
          HomeStockRecommendationBffRsp>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String symbol,
      @FrAcddField(tag: 2) String displayPrice,
      @FrAcddField(tag: 3) String gradientStartHex,
      @FrAcddField(tag: 4) String gradientEndHex});
}

/// @nodoc
class _$HomeStockRecommendationBffRspCopyWithImpl<$Res,
        $Val extends HomeStockRecommendationBffRsp>
    implements $HomeStockRecommendationBffRspCopyWith<$Res> {
  _$HomeStockRecommendationBffRspCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeStockRecommendationBffRspImplCopyWith<$Res>
    implements $HomeStockRecommendationBffRspCopyWith<$Res> {
  factory _$$HomeStockRecommendationBffRspImplCopyWith(
          _$HomeStockRecommendationBffRspImpl value,
          $Res Function(_$HomeStockRecommendationBffRspImpl) then) =
      __$$HomeStockRecommendationBffRspImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String symbol,
      @FrAcddField(tag: 2) String displayPrice,
      @FrAcddField(tag: 3) String gradientStartHex,
      @FrAcddField(tag: 4) String gradientEndHex});
}

/// @nodoc
class __$$HomeStockRecommendationBffRspImplCopyWithImpl<$Res>
    extends _$HomeStockRecommendationBffRspCopyWithImpl<$Res,
        _$HomeStockRecommendationBffRspImpl>
    implements _$$HomeStockRecommendationBffRspImplCopyWith<$Res> {
  __$$HomeStockRecommendationBffRspImplCopyWithImpl(
      _$HomeStockRecommendationBffRspImpl _value,
      $Res Function(_$HomeStockRecommendationBffRspImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? symbol = null,
    Object? displayPrice = null,
    Object? gradientStartHex = null,
    Object? gradientEndHex = null,
  }) {
    return _then(_$HomeStockRecommendationBffRspImpl(
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
    ));
  }
}

/// @nodoc

class _$HomeStockRecommendationBffRspImpl
    extends _HomeStockRecommendationBffRsp {
  const _$HomeStockRecommendationBffRspImpl(
      {@FrAcddField(tag: 1) required this.symbol,
      @FrAcddField(tag: 2) required this.displayPrice,
      @FrAcddField(tag: 3) required this.gradientStartHex,
      @FrAcddField(tag: 4) required this.gradientEndHex})
      : super._();

  @override
  @FrAcddField(tag: 1)
  final String symbol;
  @override
  @FrAcddField(tag: 2)
  final String displayPrice;
  @override
  @FrAcddField(tag: 3)
  final String gradientStartHex;
  @override
  @FrAcddField(tag: 4)
  final String gradientEndHex;

  @override
  String toString() {
    return 'HomeStockRecommendationBffRsp(symbol: $symbol, displayPrice: $displayPrice, gradientStartHex: $gradientStartHex, gradientEndHex: $gradientEndHex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeStockRecommendationBffRspImpl &&
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
      runtimeType, symbol, displayPrice, gradientStartHex, gradientEndHex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeStockRecommendationBffRspImplCopyWith<
          _$HomeStockRecommendationBffRspImpl>
      get copyWith => __$$HomeStockRecommendationBffRspImplCopyWithImpl<
          _$HomeStockRecommendationBffRspImpl>(this, _$identity);
}

abstract class _HomeStockRecommendationBffRsp
    extends HomeStockRecommendationBffRsp {
  const factory _HomeStockRecommendationBffRsp(
          {@FrAcddField(tag: 1) required final String symbol,
          @FrAcddField(tag: 2) required final String displayPrice,
          @FrAcddField(tag: 3) required final String gradientStartHex,
          @FrAcddField(tag: 4) required final String gradientEndHex}) =
      _$HomeStockRecommendationBffRspImpl;
  const _HomeStockRecommendationBffRsp._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get symbol;
  @override
  @FrAcddField(tag: 2)
  String get displayPrice;
  @override
  @FrAcddField(tag: 3)
  String get gradientStartHex;
  @override
  @FrAcddField(tag: 4)
  String get gradientEndHex;
  @override
  @JsonKey(ignore: true)
  _$$HomeStockRecommendationBffRspImplCopyWith<
          _$HomeStockRecommendationBffRspImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeOpinionArticleBffRsp {
  @FrAcddField(tag: 1)
  String get id => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get summary => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeOpinionArticleBffRspCopyWith<HomeOpinionArticleBffRsp> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeOpinionArticleBffRspCopyWith<$Res> {
  factory $HomeOpinionArticleBffRspCopyWith(HomeOpinionArticleBffRsp value,
          $Res Function(HomeOpinionArticleBffRsp) then) =
      _$HomeOpinionArticleBffRspCopyWithImpl<$Res, HomeOpinionArticleBffRsp>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String id,
      @FrAcddField(tag: 2) String headline,
      @FrAcddField(tag: 3) String summary});
}

/// @nodoc
class _$HomeOpinionArticleBffRspCopyWithImpl<$Res,
        $Val extends HomeOpinionArticleBffRsp>
    implements $HomeOpinionArticleBffRspCopyWith<$Res> {
  _$HomeOpinionArticleBffRspCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeOpinionArticleBffRspImplCopyWith<$Res>
    implements $HomeOpinionArticleBffRspCopyWith<$Res> {
  factory _$$HomeOpinionArticleBffRspImplCopyWith(
          _$HomeOpinionArticleBffRspImpl value,
          $Res Function(_$HomeOpinionArticleBffRspImpl) then) =
      __$$HomeOpinionArticleBffRspImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String id,
      @FrAcddField(tag: 2) String headline,
      @FrAcddField(tag: 3) String summary});
}

/// @nodoc
class __$$HomeOpinionArticleBffRspImplCopyWithImpl<$Res>
    extends _$HomeOpinionArticleBffRspCopyWithImpl<$Res,
        _$HomeOpinionArticleBffRspImpl>
    implements _$$HomeOpinionArticleBffRspImplCopyWith<$Res> {
  __$$HomeOpinionArticleBffRspImplCopyWithImpl(
      _$HomeOpinionArticleBffRspImpl _value,
      $Res Function(_$HomeOpinionArticleBffRspImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? headline = null,
    Object? summary = null,
  }) {
    return _then(_$HomeOpinionArticleBffRspImpl(
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
    ));
  }
}

/// @nodoc

class _$HomeOpinionArticleBffRspImpl extends _HomeOpinionArticleBffRsp {
  const _$HomeOpinionArticleBffRspImpl(
      {@FrAcddField(tag: 1) required this.id,
      @FrAcddField(tag: 2) required this.headline,
      @FrAcddField(tag: 3) required this.summary})
      : super._();

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
    return 'HomeOpinionArticleBffRsp(id: $id, headline: $headline, summary: $summary)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeOpinionArticleBffRspImpl &&
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
  _$$HomeOpinionArticleBffRspImplCopyWith<_$HomeOpinionArticleBffRspImpl>
      get copyWith => __$$HomeOpinionArticleBffRspImplCopyWithImpl<
          _$HomeOpinionArticleBffRspImpl>(this, _$identity);
}

abstract class _HomeOpinionArticleBffRsp extends HomeOpinionArticleBffRsp {
  const factory _HomeOpinionArticleBffRsp(
          {@FrAcddField(tag: 1) required final String id,
          @FrAcddField(tag: 2) required final String headline,
          @FrAcddField(tag: 3) required final String summary}) =
      _$HomeOpinionArticleBffRspImpl;
  const _HomeOpinionArticleBffRsp._() : super._();

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
  _$$HomeOpinionArticleBffRspImplCopyWith<_$HomeOpinionArticleBffRspImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomePortfolioSummaryDto {
  @FrAcddField(tag: 1)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get totalAssetLabel => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get changeRateLabel => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomePortfolioSummaryDtoCopyWith<HomePortfolioSummaryDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomePortfolioSummaryDtoCopyWith<$Res> {
  factory $HomePortfolioSummaryDtoCopyWith(HomePortfolioSummaryDto value,
          $Res Function(HomePortfolioSummaryDto) then) =
      _$HomePortfolioSummaryDtoCopyWithImpl<$Res, HomePortfolioSummaryDto>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String headline,
      @FrAcddField(tag: 2) String totalAssetLabel,
      @FrAcddField(tag: 3) String changeRateLabel});
}

/// @nodoc
class _$HomePortfolioSummaryDtoCopyWithImpl<$Res,
        $Val extends HomePortfolioSummaryDto>
    implements $HomePortfolioSummaryDtoCopyWith<$Res> {
  _$HomePortfolioSummaryDtoCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomePortfolioSummaryDtoImplCopyWith<$Res>
    implements $HomePortfolioSummaryDtoCopyWith<$Res> {
  factory _$$HomePortfolioSummaryDtoImplCopyWith(
          _$HomePortfolioSummaryDtoImpl value,
          $Res Function(_$HomePortfolioSummaryDtoImpl) then) =
      __$$HomePortfolioSummaryDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String headline,
      @FrAcddField(tag: 2) String totalAssetLabel,
      @FrAcddField(tag: 3) String changeRateLabel});
}

/// @nodoc
class __$$HomePortfolioSummaryDtoImplCopyWithImpl<$Res>
    extends _$HomePortfolioSummaryDtoCopyWithImpl<$Res,
        _$HomePortfolioSummaryDtoImpl>
    implements _$$HomePortfolioSummaryDtoImplCopyWith<$Res> {
  __$$HomePortfolioSummaryDtoImplCopyWithImpl(
      _$HomePortfolioSummaryDtoImpl _value,
      $Res Function(_$HomePortfolioSummaryDtoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? headline = null,
    Object? totalAssetLabel = null,
    Object? changeRateLabel = null,
  }) {
    return _then(_$HomePortfolioSummaryDtoImpl(
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
    ));
  }
}

/// @nodoc

class _$HomePortfolioSummaryDtoImpl extends _HomePortfolioSummaryDto {
  const _$HomePortfolioSummaryDtoImpl(
      {@FrAcddField(tag: 1) required this.headline,
      @FrAcddField(tag: 2) required this.totalAssetLabel,
      @FrAcddField(tag: 3) required this.changeRateLabel})
      : super._();

  @override
  @FrAcddField(tag: 1)
  final String headline;
  @override
  @FrAcddField(tag: 2)
  final String totalAssetLabel;
  @override
  @FrAcddField(tag: 3)
  final String changeRateLabel;

  @override
  String toString() {
    return 'HomePortfolioSummaryDto(headline: $headline, totalAssetLabel: $totalAssetLabel, changeRateLabel: $changeRateLabel)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomePortfolioSummaryDtoImpl &&
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
  _$$HomePortfolioSummaryDtoImplCopyWith<_$HomePortfolioSummaryDtoImpl>
      get copyWith => __$$HomePortfolioSummaryDtoImplCopyWithImpl<
          _$HomePortfolioSummaryDtoImpl>(this, _$identity);
}

abstract class _HomePortfolioSummaryDto extends HomePortfolioSummaryDto {
  const factory _HomePortfolioSummaryDto(
          {@FrAcddField(tag: 1) required final String headline,
          @FrAcddField(tag: 2) required final String totalAssetLabel,
          @FrAcddField(tag: 3) required final String changeRateLabel}) =
      _$HomePortfolioSummaryDtoImpl;
  const _HomePortfolioSummaryDto._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get headline;
  @override
  @FrAcddField(tag: 2)
  String get totalAssetLabel;
  @override
  @FrAcddField(tag: 3)
  String get changeRateLabel;
  @override
  @JsonKey(ignore: true)
  _$$HomePortfolioSummaryDtoImplCopyWith<_$HomePortfolioSummaryDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeStockRecommendationDto {
  @FrAcddField(tag: 1)
  String get symbol => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get displayPrice => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get gradientStartHex => throw _privateConstructorUsedError;
  @FrAcddField(tag: 4)
  String get gradientEndHex => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeStockRecommendationDtoCopyWith<HomeStockRecommendationDto>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeStockRecommendationDtoCopyWith<$Res> {
  factory $HomeStockRecommendationDtoCopyWith(HomeStockRecommendationDto value,
          $Res Function(HomeStockRecommendationDto) then) =
      _$HomeStockRecommendationDtoCopyWithImpl<$Res,
          HomeStockRecommendationDto>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String symbol,
      @FrAcddField(tag: 2) String displayPrice,
      @FrAcddField(tag: 3) String gradientStartHex,
      @FrAcddField(tag: 4) String gradientEndHex});
}

/// @nodoc
class _$HomeStockRecommendationDtoCopyWithImpl<$Res,
        $Val extends HomeStockRecommendationDto>
    implements $HomeStockRecommendationDtoCopyWith<$Res> {
  _$HomeStockRecommendationDtoCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeStockRecommendationDtoImplCopyWith<$Res>
    implements $HomeStockRecommendationDtoCopyWith<$Res> {
  factory _$$HomeStockRecommendationDtoImplCopyWith(
          _$HomeStockRecommendationDtoImpl value,
          $Res Function(_$HomeStockRecommendationDtoImpl) then) =
      __$$HomeStockRecommendationDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String symbol,
      @FrAcddField(tag: 2) String displayPrice,
      @FrAcddField(tag: 3) String gradientStartHex,
      @FrAcddField(tag: 4) String gradientEndHex});
}

/// @nodoc
class __$$HomeStockRecommendationDtoImplCopyWithImpl<$Res>
    extends _$HomeStockRecommendationDtoCopyWithImpl<$Res,
        _$HomeStockRecommendationDtoImpl>
    implements _$$HomeStockRecommendationDtoImplCopyWith<$Res> {
  __$$HomeStockRecommendationDtoImplCopyWithImpl(
      _$HomeStockRecommendationDtoImpl _value,
      $Res Function(_$HomeStockRecommendationDtoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? symbol = null,
    Object? displayPrice = null,
    Object? gradientStartHex = null,
    Object? gradientEndHex = null,
  }) {
    return _then(_$HomeStockRecommendationDtoImpl(
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
    ));
  }
}

/// @nodoc

class _$HomeStockRecommendationDtoImpl extends _HomeStockRecommendationDto {
  const _$HomeStockRecommendationDtoImpl(
      {@FrAcddField(tag: 1) required this.symbol,
      @FrAcddField(tag: 2) required this.displayPrice,
      @FrAcddField(tag: 3) required this.gradientStartHex,
      @FrAcddField(tag: 4) required this.gradientEndHex})
      : super._();

  @override
  @FrAcddField(tag: 1)
  final String symbol;
  @override
  @FrAcddField(tag: 2)
  final String displayPrice;
  @override
  @FrAcddField(tag: 3)
  final String gradientStartHex;
  @override
  @FrAcddField(tag: 4)
  final String gradientEndHex;

  @override
  String toString() {
    return 'HomeStockRecommendationDto(symbol: $symbol, displayPrice: $displayPrice, gradientStartHex: $gradientStartHex, gradientEndHex: $gradientEndHex)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeStockRecommendationDtoImpl &&
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
      runtimeType, symbol, displayPrice, gradientStartHex, gradientEndHex);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeStockRecommendationDtoImplCopyWith<_$HomeStockRecommendationDtoImpl>
      get copyWith => __$$HomeStockRecommendationDtoImplCopyWithImpl<
          _$HomeStockRecommendationDtoImpl>(this, _$identity);
}

abstract class _HomeStockRecommendationDto extends HomeStockRecommendationDto {
  const factory _HomeStockRecommendationDto(
          {@FrAcddField(tag: 1) required final String symbol,
          @FrAcddField(tag: 2) required final String displayPrice,
          @FrAcddField(tag: 3) required final String gradientStartHex,
          @FrAcddField(tag: 4) required final String gradientEndHex}) =
      _$HomeStockRecommendationDtoImpl;
  const _HomeStockRecommendationDto._() : super._();

  @override
  @FrAcddField(tag: 1)
  String get symbol;
  @override
  @FrAcddField(tag: 2)
  String get displayPrice;
  @override
  @FrAcddField(tag: 3)
  String get gradientStartHex;
  @override
  @FrAcddField(tag: 4)
  String get gradientEndHex;
  @override
  @JsonKey(ignore: true)
  _$$HomeStockRecommendationDtoImplCopyWith<_$HomeStockRecommendationDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$HomeOpinionArticleDto {
  @FrAcddField(tag: 1)
  String get id => throw _privateConstructorUsedError;
  @FrAcddField(tag: 2)
  String get headline => throw _privateConstructorUsedError;
  @FrAcddField(tag: 3)
  String get summary => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeOpinionArticleDtoCopyWith<HomeOpinionArticleDto> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeOpinionArticleDtoCopyWith<$Res> {
  factory $HomeOpinionArticleDtoCopyWith(HomeOpinionArticleDto value,
          $Res Function(HomeOpinionArticleDto) then) =
      _$HomeOpinionArticleDtoCopyWithImpl<$Res, HomeOpinionArticleDto>;
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String id,
      @FrAcddField(tag: 2) String headline,
      @FrAcddField(tag: 3) String summary});
}

/// @nodoc
class _$HomeOpinionArticleDtoCopyWithImpl<$Res,
        $Val extends HomeOpinionArticleDto>
    implements $HomeOpinionArticleDtoCopyWith<$Res> {
  _$HomeOpinionArticleDtoCopyWithImpl(this._value, this._then);

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
    return _then(_value.copyWith(
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
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeOpinionArticleDtoImplCopyWith<$Res>
    implements $HomeOpinionArticleDtoCopyWith<$Res> {
  factory _$$HomeOpinionArticleDtoImplCopyWith(
          _$HomeOpinionArticleDtoImpl value,
          $Res Function(_$HomeOpinionArticleDtoImpl) then) =
      __$$HomeOpinionArticleDtoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@FrAcddField(tag: 1) String id,
      @FrAcddField(tag: 2) String headline,
      @FrAcddField(tag: 3) String summary});
}

/// @nodoc
class __$$HomeOpinionArticleDtoImplCopyWithImpl<$Res>
    extends _$HomeOpinionArticleDtoCopyWithImpl<$Res,
        _$HomeOpinionArticleDtoImpl>
    implements _$$HomeOpinionArticleDtoImplCopyWith<$Res> {
  __$$HomeOpinionArticleDtoImplCopyWithImpl(_$HomeOpinionArticleDtoImpl _value,
      $Res Function(_$HomeOpinionArticleDtoImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? headline = null,
    Object? summary = null,
  }) {
    return _then(_$HomeOpinionArticleDtoImpl(
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
    ));
  }
}

/// @nodoc

class _$HomeOpinionArticleDtoImpl extends _HomeOpinionArticleDto {
  const _$HomeOpinionArticleDtoImpl(
      {@FrAcddField(tag: 1) required this.id,
      @FrAcddField(tag: 2) required this.headline,
      @FrAcddField(tag: 3) required this.summary})
      : super._();

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
    return 'HomeOpinionArticleDto(id: $id, headline: $headline, summary: $summary)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeOpinionArticleDtoImpl &&
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
  _$$HomeOpinionArticleDtoImplCopyWith<_$HomeOpinionArticleDtoImpl>
      get copyWith => __$$HomeOpinionArticleDtoImplCopyWithImpl<
          _$HomeOpinionArticleDtoImpl>(this, _$identity);
}

abstract class _HomeOpinionArticleDto extends HomeOpinionArticleDto {
  const factory _HomeOpinionArticleDto(
          {@FrAcddField(tag: 1) required final String id,
          @FrAcddField(tag: 2) required final String headline,
          @FrAcddField(tag: 3) required final String summary}) =
      _$HomeOpinionArticleDtoImpl;
  const _HomeOpinionArticleDto._() : super._();

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
  _$$HomeOpinionArticleDtoImplCopyWith<_$HomeOpinionArticleDtoImpl>
      get copyWith => throw _privateConstructorUsedError;
}
