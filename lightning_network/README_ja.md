# Lightning Network Route Optimization Using Quantum Annealing

Lightning Network のトランザクション経路最適化を量子アニーリング（Fixstars Amplify）で実現する実装です。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📖 概要

このプロジェクトは、2018年度未踏ターゲット事業「アニーリングを用いたブロックチェーンの高速化技術の開発」で発表された研究を実装したものです。

> English README is available: [README.md](README.md)

詳細については、以下のドキュメントを参照してください：
- [論文要約（日本語）](docs/paper_summary.md)
- [実装・検証レポート（日本語）](IMPLEMENTATION_REPORT.md)
- [GitHub公開チェックリスト（日本語）](GITHUB_CHECKLIST.md)

## 🚀 クイックスタート

### インストール

```bash
cd lightning_network
pip install -r requirements.txt
```

### APIトークンの設定

```bash
cp .env.example .env
# .envファイルを編集してAPIトークンを設定
```

### 実行

```bash
# 基本例（小規模）
python examples/basic_example.py

# 論文再現（大規模）
python examples/paper_replication.py
```

## 📚 ドキュメント（日本語）

- [論文要約](docs/paper_summary.md) - 元論文の詳細な解説
- [実装レポート](IMPLEMENTATION_REPORT.md) - 実装の詳細と検証結果
- [GitHub公開チェックリスト](GITHUB_CHECKLIST.md) - 公開準備の確認項目

## 🧪 テスト

```bash
pytest tests/ -v
```

全テスト合格: ✅ 6/6

## 📄 ライセンス

MIT License
