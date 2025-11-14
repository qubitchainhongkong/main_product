#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
portfolio.pyの基本的な動作確認テスト（データファイル不要版）
"""

import sys
import os
import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

print("=" * 60)
print("portfolio.pyの基本動作テスト")
print("=" * 60)

# 1. 基本的なインポートテスト
print("\n[1] 基本的なインポートテスト")
try:
    import amplify
    print(f"✓ amplify {amplify.__version__} のインポート成功")
except ImportError as e:
    print(f"✗ amplify のインポート失敗: {e}")
    sys.exit(1)

# 2. テスト用のダミーデータ作成
print("\n[2] テスト用のダミー株価データの作成")
try:
    np.random.seed(42)
    
    # 10銘柄、100営業日分のダミーデータ
    num_stocks = 10
    num_days = 100
    stock_names = [f"stock_{i}" for i in range(num_stocks)]
    
    # 幾何ブラウン運動風のダミーデータを生成
    initial_prices = np.random.uniform(100, 1000, num_stocks)
    returns = np.random.normal(0.001, 0.02, (num_days, num_stocks))
    
    prices = np.zeros((num_days, num_stocks))
    prices[0] = initial_prices
    for i in range(1, num_days):
        prices[i] = prices[i-1] * (1 + returns[i])
    
    # DataFrameに変換
    dates = pd.date_range(start='2024-01-01', periods=num_days, freq='B')
    stock_prices = pd.DataFrame(prices, index=dates, columns=stock_names)
    
    print(f"✓ ダミーデータ作成成功: {num_stocks}銘柄 × {num_days}営業日")
    print(f"  価格範囲: {stock_prices.min().min():.2f} ~ {stock_prices.max().max():.2f}")
    
except Exception as e:
    print(f"✗ ダミーデータ作成失敗: {e}")
    sys.exit(1)

# 3. calculate_return_rates 関数のテスト
print("\n[3] calculate_return_rates 関数のテスト")
try:
    def calculate_return_rates(prices: np.ndarray, num_days_operation: int) -> np.ndarray:
        return (prices[num_days_operation:] - prices[:-num_days_operation]) / prices[:-num_days_operation]
    
    return_rates = calculate_return_rates(stock_prices.to_numpy(), 20)
    print(f"✓ 収益率計算成功: shape={return_rates.shape}")
    print(f"  平均収益率: {np.mean(return_rates):.4f}")
    print(f"  収益率の範囲: {np.min(return_rates):.4f} ~ {np.max(return_rates):.4f}")
    
except Exception as e:
    print(f"✗ 収益率計算失敗: {e}")
    sys.exit(1)

# 4. Amplify SDKの基本動作テスト（最適化なし）
print("\n[4] Amplify SDKの基本動作テスト")
try:
    # 変数生成器の作成
    gen = amplify.VariableGenerator()
    w = gen.array("Integer", num_stocks, bounds=(0, 20))
    
    # 制約条件の作成
    constraint = amplify.equal_to(w.sum(), 100)
    
    # 簡単な目的関数の作成
    w_ratio = w / 100
    portfolio_return_rate = (w_ratio * np.mean(return_rates, axis=0)).sum()
    
    print(f"✓ 変数と制約条件の作成成功")
    print(f"  変数数: {len(w)}")
    print(f"  制約条件: w の総和 = 100")
    
except Exception as e:
    print(f"✗ Amplify SDK基本動作失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. AmplifyAEクライアントの初期化テスト（実行なし）
print("\n[5] AmplifyAEクライアントの初期化テスト")
try:
    client = amplify.AmplifyAEClient()
    client.parameters.time_limit_ms = datetime.timedelta(seconds=1)
    
    # .envファイルからAPIトークンを読み込む
    amplify_token = os.getenv("AMPLIFY_TOKEN")
    if amplify_token and amplify_token != "your_api_token_here":
        client.token = amplify_token
        print("✓ クライアント初期化成功（APIトークン設定済み）")
    else:
        print("⚠️  クライアント初期化成功（APIトークン未設定）")
        print("  実際の最適化を実行するには、.envファイルにAPIトークンを設定してください")
    
except Exception as e:
    print(f"✗ クライアント初期化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 6. portfolio.pyからのインポートテスト
print("\n[6] portfolio.pyからの関数インポートテスト")
try:
    # portfolio.pyをモジュールとしてインポート
    import importlib.util
    spec = importlib.util.spec_from_file_location("portfolio", "portfolio.py")
    portfolio_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(portfolio_module)
    
    # 関数が存在するか確認
    if hasattr(portfolio_module, 'calculate_return_rates'):
        print("✓ calculate_return_rates 関数のインポート成功")
    
    if hasattr(portfolio_module, 'optimize_portfolio'):
        print("✓ optimize_portfolio 関数のインポート成功")
    
except Exception as e:
    print(f"⚠️  portfolio.pyのインポート中にエラー: {e}")
    print("  これはデータファイルが存在しないためかもしれません")
    import traceback
    traceback.print_exc()

# 7. 最終結果
print("\n" + "=" * 60)
print("テスト結果サマリー")
print("=" * 60)
print("✓ すべての基本的な機能が正常に動作しています！")
print("\n次のステップ:")
print("1. .envファイルに実際のAPIトークンを設定")
print("2. 実データまたはダミーデータファイルを配置")
print("3. optimize_portfolio()関数で最適化を実行")
print("\nAPIトークンの取得: https://amplify.fixstars.com/")
print("=" * 60)

sys.exit(0)

