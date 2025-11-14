# ポートフォリオ最適化

Fixstars Amplify AE を使用した株式ポートフォリオ最適化のデモンストレーションプログラムです。

## 概要

このプログラムは、Fixstars Amplify を利用してポートフォリオを最適化します。最適化にはヒストリカルデータ方式に基づく推計値を用います。

- 株価データの取得
- 最適ポートフォリオ求解のための定式化及びソルバの実装
- 最適化の実行と評価
- 運用シミュレーション

## 必要な環境

- Python 3.8以上
- pip（Pythonパッケージマネージャー）

## セットアップ手順

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. Fixstars Amplify AE のAPIトークンの取得と設定

#### 2.1 APIトークンの取得

1. [Fixstars Amplify](https://amplify.fixstars.com/) にアクセス
2. アカウントを作成してログイン
3. APIトークンを取得

#### 2.2 .envファイルの設定

`.env`ファイルを開き、取得したAPIトークンを設定します:

```bash
# .envファイルの内容
AMPLIFY_TOKEN=ここに取得したAPIトークンを貼り付ける
```

**注意**: `.env`ファイルはGitにコミットされません（セキュリティのため）。

## 動作確認

### パッケージのインポートテスト

```bash
python3 test_imports.py
```

すべてのパッケージが正常にインポートできることを確認します。

### .envファイルの読み込みテスト

```bash
python3 test_env.py
```

APIトークンが正常に読み込まれることを確認します。

### メインプログラムの実行

```bash
python3 portfolio.py
```

**注意**: 
- このプログラムは、`../../../storage/portfolio/dummy_stock_price.csv` のパスにダミーデータを期待しています。
- データファイルが見つからない場合は、`load_stock_prices()`関数内のパスを適切に変更してください。
- Jupyter Notebookで実行することを想定したコードのため、通常のPythonスクリプトとして実行する場合は調整が必要な場合があります。

## ファイル構成

```
.
├── portfolio.py           # メインプログラム
├── requirements.txt       # 必要なパッケージリスト
├── .env                   # APIトークン設定ファイル（要作成・Git管理外）
├── .env.example          # .envファイルのテンプレート
├── test_imports.py       # パッケージインポートテスト
├── test_env.py           # 環境変数読み込みテスト
└── README.md             # このファイル
```

## トラブルシューティング

### パッケージのインポートエラー

```bash
pip install -r requirements.txt
```

でパッケージを再インストールしてください。

### APIトークンが読み込まれない

1. `.env`ファイルが存在することを確認
2. `.env`ファイルに`AMPLIFY_TOKEN`が正しく記載されていることを確認
3. `test_env.py`を実行して確認

### データファイルが見つからない

`portfolio.py`の`load_stock_prices()`関数内のパスを、実際のデータファイルの場所に合わせて変更してください。

```python
def load_stock_prices() -> pd.DataFrame:
    return pd.read_csv(
        "your/data/path/dummy_stock_price.csv",  # ここを変更
        index_col="Date",
        parse_dates=True,
    )
```

## 注意事項

※本サンプルプログラムは、Fixstars Amplify を利用した最適化アプリケーションのデモンストレーションを目的としています。この情報を基に実際の運用を行う際には、ユーザー自身の責任において実施してください。

## ライセンス

このプログラムの利用については、Fixstars Amplify の利用規約に従ってください。

