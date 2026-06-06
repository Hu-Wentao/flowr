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
          help: 'Optional path for the generated .proto file.',
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
  final builder = const ProtoSchemaBuilder();

  try {
    final schema = extractor.extractFromFile(input);
    if (!schema.supported) {
      stderr.writeln(
        schema.reason ?? 'The contract is not eligible for protobuf output.',
      );
      exitCode = 2;
      return;
    }

    final proto = builder.build(schema);
    final output = args['output'] as String?;
    if (output == null || output.trim().isEmpty) {
      stdout.write(proto);
      return;
    }

    final file = File(output);
    await file.parent.create(recursive: true);
    await file.writeAsString(proto);
  } catch (error) {
    stderr.writeln(error);
    exitCode = 1;
  }
}
