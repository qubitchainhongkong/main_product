#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
必要なパッケージがインポートできるかテストするスクリプト
"""

import sys

def test_imports():
    """必要なパッケージのインポートをテストする"""
    print("=" * 60)
    print("パッケージのインポートテスト")
    print("=" * 60)
    
    success = True
    
    # 基本パッケージ
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
    except ImportError as e:
        print(f"✗ pandas のインポートに失敗: {e}")
        success = False
    
    try:
        import numpy as np
        print(f"✓ numpy {np.__version__}")
    except ImportError as e:
        print(f"✗ numpy のインポートに失敗: {e}")
        success = False
    
    try:
        import matplotlib
        print(f"✓ matplotlib {matplotlib.__version__}")
    except ImportError as e:
        print(f"✗ matplotlib のインポートに失敗: {e}")
        success = False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv")
    except ImportError as e:
        print(f"✗ python-dotenv のインポートに失敗: {e}")
        success = False
    
    try:
        import amplify
        print(f"✓ amplify {amplify.__version__}")
    except ImportError as e:
        print(f"✗ amplify のインポートに失敗: {e}")
        success = False
    
    print("=" * 60)
    
    if success:
        print("\n✓ すべてのパッケージのインポートに成功しました！")
        return 0
    else:
        print("\n✗ いくつかのパッケージのインポートに失敗しました。")
        print("\n以下のコマンドでインストールしてください:")
        print("pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(test_imports())

