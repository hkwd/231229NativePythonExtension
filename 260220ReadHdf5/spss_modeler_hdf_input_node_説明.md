# SPSS Modeler 拡張入力ノード - HDF5ファイル読み込みスクリプト

## 概要
このスクリプトは、SPSS ModelerでHDF5ファイル（`c:\temp6\sample_sensor_data.h5`）の`sensor_data`グループからデータを読み込むための拡張入力ノードです。

## 主な機能

### 1. 汎用的なデータ読み込み
- HDFファイル内の`sensor_data`グループから全てのデータセットを自動的に検出
- データセット名、データ型を動的に取得して処理
- 各データセットをDataFrameの列として読み込み

### 2. データ型の自動判定
スクリプトは各データセットのNumPy dtype に基づいて、SPSS Modelerのストレージタイプと測定タイプを自動的に決定します：

| NumPy dtype | SPSS ストレージ | SPSS 測定 |
|-------------|----------------|-----------|
| float64, float32 | real | continuous |
| int64, int32, int16, int8 | integer | continuous |
| object, Unicode, String | string | nominal |

### 3. 2段階の処理フロー

#### フェーズ1: データモデルの計算（`isComputeDataModelOnly() == True`）
```python
if modelerpy.isComputeDataModelOnly():
    # メタデータのみを取得
    # データセットの構造を分析
    # 出力データモデルを構築
    modelerpy.setOutputDataModel(outputDataModel)
```

このフェーズでは：
- HDFファイルを開いてメタデータのみを読み取る
- 各データセットの名前とデータ型を取得
- `modelerpy.Field`オブジェクトを作成してデータモデルに追加
- `setOutputDataModel()`でSPSS Modelerにメタデータを送信

#### フェーズ2: 実データの読み込み（`isComputeDataModelOnly() == False`）
```python
else:
    # 実際のデータを読み込む
    # Pandas DataFrameに変換
    modelerpy.writePandasDataframe(outputData)
```

このフェーズでは：
- HDFファイルから実際のデータを読み込む
- オブジェクト型データ（バイト列）を文字列にデコード
- Pandas DataFrameを作成
- `writePandasDataframe()`でSPSS Modelerにデータを送信

## 使用しているネイティブPython API

### データモデル用API
- **`modelerpy.isComputeDataModelOnly()`**: 現在の実行がデータモデルのみを計算するかを確認
- **`modelerpy.setOutputDataModel(dataModel)`**: 出力データモデルをSPSS Modelerに設定

### メタデータ用API
- **`modelerpy.DataModel(fields)`**: データモデルオブジェクトを作成
- **`modelerpy.Field(name, storage, measure)`**: フィールドメタデータを定義
- **`DataModel.addField(field)`**: データモデルにフィールドを追加

### 入出力データセット用API
- **`modelerpy.writePandasDataframe(df)`**: Pandas DataFrameをSPSS Modelerに書き込む

## スクリプトの構造

```
1. インポート
   ├─ modelerpy (SPSS Modeler API)
   ├─ h5py (HDF5ファイル操作)
   ├─ pandas (データフレーム処理)
   └─ numpy (数値計算)

2. 設定
   ├─ HDF_FILE_PATH: HDFファイルのパス
   └─ GROUP_NAME: 読み込むグループ名

3. データモデル計算フェーズ
   ├─ HDFファイルを開く
   ├─ グループの存在確認
   ├─ 各データセットのメタデータを取得
   ├─ データ型に基づいてフィールドを作成
   └─ 出力データモデルを設定

4. データ読み込みフェーズ
   ├─ HDFファイルを開く
   ├─ グループの存在確認
   ├─ 各データセットのデータを読み込む
   ├─ オブジェクト型データをデコード
   ├─ Pandas DataFrameを作成
   └─ データをSPSS Modelerに書き込む
```

## 対象データセット（sample_sensor_data.h5）

このスクリプトは以下のデータセットを読み込みます：

| データセット名 | データ型 | 形状 | SPSS ストレージ | SPSS 測定 |
|---------------|---------|------|----------------|-----------|
| pressure | float64 | (1000,) | real | continuous |
| rotation_speed | float64 | (1000,) | real | continuous |
| status | object | (1000,) | string | nominal |
| temperature | float64 | (1000,) | real | continuous |
| timestamp | object | (1000,) | string | nominal |
| vibration | float64 | (1000,) | real | continuous |

## カスタマイズ方法

### 1. 異なるHDFファイルを読み込む場合
```python
HDF_FILE_PATH = r'c:\your\path\to\file.h5'
```

### 2. 異なるグループを読み込む場合
```python
GROUP_NAME = 'your_group_name'
```

### 3. データ型マッピングをカスタマイズする場合
データ型判定のロジック（31-44行目）を修正してください。

### 4. 特定のデータセットのみを読み込む場合
```python
# 読み込むデータセットのリストを定義
DATASETS_TO_LOAD = ['temperature', 'pressure', 'vibration']

# ループ内で条件を追加
for dataset_name in group.keys():
    if dataset_name not in DATASETS_TO_LOAD:
        continue
    # 処理を続行...
```

## 注意事項

1. **シバンは不要**: SPSS Modelerの拡張ノードでは、スクリプトの先頭に`#!/usr/bin/env python`などのシバンは不要です。

2. **エラーハンドリング**: グループが存在しない場合は`ValueError`を発生させます。

3. **メモリ使用**: 大きなデータセットの場合、全データをメモリに読み込むため、メモリ使用量に注意してください。

4. **文字エンコーディング**: オブジェクト型データはUTF-8でデコードを試みます。失敗した場合は`str()`で文字列に変換します。

## 参考資料

- [IBM SPSS Modeler - ネイティブ Python API](https://www.ibm.com/docs/ja/spss-modeler/18.5.0?topic=spark-native-python-apis)
- [h5py ドキュメント](https://docs.h5py.org/)
- [Pandas ドキュメント](https://pandas.pydata.org/docs/)

## ライセンス

このスクリプトはSPSS Modelerの拡張ノードとして使用するためのサンプルコードです。