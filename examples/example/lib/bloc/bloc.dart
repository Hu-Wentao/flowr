/// Bloc-based examples for [ValueStreamBuilder], [ValueStreamConsumer],
/// and [ValueStreamListener] using the new [bloc] parameter.
///
/// The `bloc` parameter is the recommended replacement for the legacy
/// `stream` parameter (rxdart-based). These widgets internally delegate
/// to Flutter Bloc's `BlocBuilder`, `BlocConsumer`, and `BlocListener`.
///
/// ## Key differences
///
/// | Aspect | Old (`stream:`) | New (`bloc:`) |
/// |--------|-----------------|---------------|
/// | Source | `ValueStream<T>` (rxdart) | `StateStreamable<T>` (bloc) |
/// | Compatibility | Legacy | Recommended |
/// | Internal impl | Direct listener | Delegates to Bloc widgets |
///
/// ## Example files
///
/// - [value_stream_builder/vsb_basic] — [ValueStreamBuilder] with `bloc`
/// - [value_stream_consumer/vsc_basic] — [ValueStreamConsumer] with `bloc`
/// - [value_stream_listener/vsl_basic] — [ValueStreamListener] with `bloc`
library;

export 'shared/counter_vm.dart';
export 'value_stream_builder/vsb_basic.dart';
export 'value_stream_consumer/vsc_basic.dart';
export 'value_stream_listener/vsl_basic.dart';