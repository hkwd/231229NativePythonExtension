# IBM SPSS Modeler Server ログパーサー

IBM SPSS Modeler Server の `server_logging.log` ファイルを読み込み、構造化されたデータフレームに変換する Python 拡張ノードスクリプトです。

## 概要

このスクリプトは、SPSS Modeler の拡張入力ノードとして動作し、サーバーログファイルを解析して以下の情報を抽出します:

- 日時とミリ秒
- プロセスID、スレッドID
- ログレベル（INFO、WARNING、ERROR など）
- コンポーネント名
- モジュール名
- メッセージID とメッセージ本文
- ユーザー名（セッション情報から自動抽出・補完）
- ソースファイルパス

## 機能

### 1. ログ行のパース

正規表現を使用して、以下の形式のログ行を解析します:

```
2024-01-01 12:34:56,789  12345 0x1a2b3c4d INFO  [Component] Module MSGID0001I: Message text
```

### 2. ユーザー名の自動補完

- `AEQMC0007I` メッセージからセッション開始情報を抽出
- プロセスIDとユーザー名のマッピングを作成
- 同じプロセスIDを持つすべてのログレコードにユーザー名を伝播

### 3. メッセージIDの分離

メッセージから ID 部分（例: `AEQMC0075I`）とテキスト部分を自動的に分離します。

## 出力データモデル

| フィールド名 | データ型 | 測定尺度 | 説明 |
|------------|---------|---------|------|
| datetime | timestamp | continuous | ログのタイムスタンプ |
| millisecond | integer | continuous | ミリ秒 |
| process_id | integer | continuous | プロセスID |
| thread_id | string | nominal | スレッドID（16進数） |
| log_level | string | nominal | ログレベル（INFO、WARNING など） |
| component | string | nominal | コンポーネント名 |
| module | string | nominal | モジュール名 |
| message_id | string | nominal | メッセージID（例: AEQMC0075I） |
| message | string | nominal | メッセージ本文 |
| user_name | string | nominal | ユーザー名 |
| source_file | string | nominal | ソースログファイルのパス |

## 使用方法

### 1. ログファイルパスの設定

スクリプト内の `FILE_1` 変数を編集して、読み込むログファイルのパスを指定します:

```python
FILE_1 = r"/usr/IBM/SPSS/ModelerServer/19.0/log/server_logging.log"
```

### 2. SPSS Modeler での使用

1. SPSS Modeler でストリームを開く
2. 「ソース」パレットから「拡張入力」ノードをキャンバスに配置
3. ノードをダブルクリックして設定を開く
4. 「Python」を選択し、このスクリプトファイルを指定
5. ノードを実行してログデータを読み込む

### 3. データの活用例

読み込んだデータは、以下のような分析に活用できます:

- ユーザー別のセッション分析
- エラーログの集計とトレンド分析
- プロセスIDごとの処理時間分析
- コンポーネント別のログ量分析

## 技術仕様

### 依存ライブラリ

- `modelerpy`: IBM SPSS Modeler Python API
- `pandas`: データフレーム操作
- `re`: 正規表現処理

### 正規表現パターン

#### ログ行パターン (`LOG_PATTERN`)
```
^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+)\s+(\d+)\s+(0x[0-9a-fA-F]+)\s+(\w+)\s+\[([^\]]+)\]\s+(\S+)\s+(.*)
```

#### メッセージID分離パターン (`MSG_SPLIT_PATTERN`)
```
^([A-Z0-9]+):\s*(.*)
```

#### セッション情報抽出パターン (`SESSION_PATTERN`)
```
Session\s+(\d+)\s+\(([^@]+)@
```

#### ユーザー名抽出パターン (`USER_PATTERN`)
```
(?:for user|User name):\s*(\S+)
```

## 注意事項

- パターンに一致しない行（継続行など）も保持されますが、構造化フィールドは `None` になります
- `datetime` 列は自動的に pandas の datetime 型に変換されます
- 整数列の欠損値は `-1` で埋められます
- UTF-8 BOM 付きファイルにも対応しています

## ライセンス

このスクリプトは IBM SPSS Modeler 環境での使用を想定しています。

## 作成者

IBM SPSS Modeler ユーザー向けに作成されたログ解析ツールです。

## バージョン履歴

- 初版: IBM SPSS Modeler Server 19.0 のログ形式に対応