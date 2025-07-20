# 关键场景用法指南

## 嵌套Provider
> 使用FrProvider注入VM

如果一个Column中包含两个相同类型的Field, 使用Provider通常会导致context无法找到正确的VM.

### 错误用法
```dart
FrProvider.multi([
  FrProvider((c) => FieldViewModel()),
  FrProvider((c) => FieldViewModel()),
  ],
  child: Column(
  children: [
    FieldView(title: 'name'),
    FieldView(title: 'note'),
  ]
  )
)
```

### 正确用法
```dart
Column(
  children: [
    FrProvider(
      (c) => FieldViewModel(),
      child: FieldView(title: 'name')),
    FrProvider(
      (c) => FieldViewModel(),
      child: FieldView(title: 'note')),
  ]
)
```

### 此外, 对于`FieldViewModel`存在于另一个`FormViewModel`内部的情况: 
A. 内部创建
可以由`FormViewModel`内部创建两个`FieldViewModel`, 同时在Widget树中使用 `FrProvider.value` 来提供给 `FieldView`。

B. @Since(‘0.3.0’) 外部传入
也可以由`FrProvider`创建, 再通过 `FrProvider::onCreated` 回调,将 `FieldViewModel`实例传入`FormViewModel`

## 去重(distinct)
> 当Model不使用@immutable, 通过 return old..field = value; 的方式更新时.

这种情况下, VM.value (Model的实例), 总是同一个对象, 这导致 stream.distinct() 每次都在用同一个对象进行比较, 结果是每次都不会触发更新.
### 场景
```dart
// update后, vm.value 仍然是原来的对象
vm.update((old) => old..field = value);
```

### 错误用法
```dart
vm.stream.distinct().listen((data) {
  // field 更新时, 不会触发 listen回调
});
```
### 正确用法
```dart
vm.stream.map((e)=>e.field).distinct().listen((fieldData) {
  // 通过映射为field, distinct将会比较每次产生的field对象
  // 因此field 更新时, 会触发 listen回调; 得到 String fieldData 想着想
});

@Since('0.15.0')
vm.stream.distinctBy((e) => e.field).listen((data) {
  // 使用 distinctBy, 直接指定比较的字段
  // 因此field 更新时, 会触发 listen回调; 得到完整的 Model data 对象
});
```

## 监听 ChangeNotifier (TextEditingController, ScrollController, FocusNode...)

直接将Controller放置到 VM内部, 作为字段. 等同于其他内嵌VM;
通过listen方法, 将值变化提交到Model中

```dart
late fianl TextEditingController
ctrlNote;

FormViewModel() {
  ctrlNote = autoDisposeNotifier(TextEditingController()).listen((ntf) {
    // value 是 TextEditingController 的变化
    // 这里可以将 ctrlNote.text 提交到 Model 中
    update((old) => old..note = ntf.text);
  },
  where: debounceMs, // 设置debounce, 默认200ms
  );
}

```