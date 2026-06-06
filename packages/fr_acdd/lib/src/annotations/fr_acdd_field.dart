class FrAcddField {
  const FrAcddField({
    this.wireName,
    this.tag,
    this.nestedRef,
    this.include = true,
  });

  final String? wireName;
  final int? tag;
  final Type? nestedRef;
  final bool include;
}
