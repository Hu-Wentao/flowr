import 'dart:io';

import 'package:args/args.dart';
import 'package:fr_acdd/fr_acdd.dart';

Future<void> main(List<String> arguments) async {
  final parser =
      ArgParser()
        ..addOption(
          'input',
          abbr: 'i',
          help: 'Path to the annotated contract file.',
        )
        ..addOption(
          'output',
          abbr: 'o',
          help:
              'Optional path for the generated output file (.proto or .json5).',
        )
        ..addOption(
          'format',
          abbr: 'f',
          allowed: ['proto', 'json5'],
          defaultsTo: 'proto',
          help: 'Final export type for the shared BFF DTO analysis.',
        )
        ..addFlag('help', abbr: 'h', negatable: false, help: 'Show CLI help.');

  late final ArgResults args;
  try {
    args = parser.parse(arguments);
  } on FormatException catch (error) {
    stderr
      ..writeln(error.message)
      ..writeln(parser.usage);
    exitCode = 64;
    return;
  }

  if (args['help'] == true) {
    stdout.writeln(parser.usage);
    return;
  }

  final input = args['input'] as String?;
  if (input == null || input.trim().isEmpty) {
    stderr
      ..writeln('Missing required --input.')
      ..writeln(parser.usage);
    exitCode = 64;
    return;
  }

  final extractor = ContractExtractor();

  try {
    final schema = extractor.extractFromFile(input);
    if (!schema.supported) {
      stderr.writeln(
        schema.reason ?? 'The contract is not eligible for BFF DTO export.',
      );
      exitCode = 2;
      return;
    }

    final format = args['format'] as String? ?? 'proto';
    final outputContent = switch (format) {
      'json5' => const Json5SchemaBuilder().build(schema),
      'proto' => const ProtoSchemaBuilder().build(schema),
      _ => throw StateError('Unsupported output format `$format`.'),
    };
    final output = args['output'] as String?;
    if (output == null || output.trim().isEmpty) {
      stdout.write(outputContent);
      return;
    }

    final file = File(output);
    await file.parent.create(recursive: true);
    await file.writeAsString(outputContent);
  } catch (error) {
    stderr.writeln(error);
    exitCode = 1;
  }
}
