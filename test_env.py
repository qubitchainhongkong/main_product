#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.envファイルの読み込みをテストするスクリプト
"""

import os
import sys

def test_env():
    """環境変数のテスト"""
    print("=" * 60)
    print(".envファイルの読み込みテスト")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        
        # .envファイルを読み込む
        load_dotenv()
        
        # AMPLIFY_TOKEN を取得
        amplify_token = os.getenv("AMPLIFY_TOKEN")
        
        if amplify_token:
            # トークンの一部を表示（セキュリティのため全部は表示しない）
            if amplify_token == "your_api_token_here":
                print("⚠️  AMPLIFY_TOKEN は設定されていますが、デフォルト値のままです。")
                print("\n.envファイルに実際のAPIトークンを設定してください:")
                print("1. https://amplify.fixstars.com/ からAPIトークンを取得")
                print("2. .envファイルを開く")
                print("3. AMPLIFY_TOKEN=your_api_token_here を実際のトークンに置き換える")
                return 1
            else:
                # 最初の数文字だけ表示
                token_preview = amplify_token[:8] + "..." if len(amplify_token) > 8 else amplify_token
                print(f"✓ AMPLIFY_TOKEN が正常に読み込まれました: {token_preview}")
                print("\n✓ .envファイルの設定は正常です！")
                return 0
        else:
            print("✗ AMPLIFY_TOKEN が見つかりません。")
            print("\n.envファイルを作成し、以下の内容を記述してください:")
            print("AMPLIFY_TOKEN=your_api_token_here")
            return 1
            
    except ImportError:
        print("✗ python-dotenv がインストールされていません。")
        print("\n以下のコマンドでインストールしてください:")
        print("pip install python-dotenv")
        return 1

if __name__ == "__main__":
    sys.exit(test_env())

