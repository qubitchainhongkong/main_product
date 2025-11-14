#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paper Replication: Lightning Network Route Optimization

This example replicates the exact settings from the academic paper:
"Development of Blockchain Acceleration Technology Using Annealing"
(2018 Mitou Target Program)

論文の設定:
- ノード数: 2000
- チャネル数: 20000
- トランザクション数: 4
- 金額範囲: 200-600
- 候補経路数: 3
- α: 2
- β: 平均金額の二乗 × 100
"""

import sys
import os
import time

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph_generator import LightningNetworkGraph
from src.route_finder import RouteFinder
from src.optimizer import RouteOptimizer


def main():
    """メイン関数"""
    
    print("=" * 70)
    print("Lightning Network Route Optimization - Paper Replication")
    print("2018年度未踏ターゲット事業")
    print("アニーリングを用いたブロックチェーンの高速化技術の開発")
    print("=" * 70)
    
    # ステップ1: グラフの生成（論文と同じ設定）
    print("\n[ステップ1] Lightning Network グラフの生成")
    print("  設定: ノード数=2000, チャネル数=20000")
    
    start_time = time.time()
    
    ln_graph = LightningNetworkGraph(
        num_nodes=2000,
        num_channels=20000,
        capacity_range=(200, 900),
        seed=42
    )
    
    graph = ln_graph.generate()
    
    graph_gen_time = time.time() - start_time
    print(f"  グラフ生成時間: {graph_gen_time:.2f}秒")
    
    stats = ln_graph.get_statistics()
    
    print(f"\n  グラフ統計:")
    print(f"    ノード数: {stats['num_nodes']}")
    print(f"    チャネル数: {stats['num_edges']}")
    print(f"    平均次数: {stats['avg_degree']:.2f} (各ノードに約15-30のチャネル)")
    print(f"    次数範囲: {stats['min_degree']} - {stats['max_degree']}")
    print(f"    平均キャパシティ: {stats['avg_capacity']:.2f}")
    print(f"    キャパシティ範囲: {stats['min_capacity']} - {stats['max_capacity']}")
    print(f"    平均手数料: {stats['avg_fee']:.4f}")
    print(f"    連結性: {'✓ 連結' if stats['is_connected'] else '✗ 非連結'}")
    
    # ステップ2: トランザクションの生成
    print("\n[ステップ2] トランザクションの生成")
    print("  設定: トランザクション数=4, 金額範囲=200-600")
    
    route_finder = RouteFinder(graph, num_route_candidates=3)
    transactions = route_finder.generate_transactions(
        num_transactions=4,
        amount_range=(200, 600),
        seed=42
    )
    
    print(f"\n  生成されたトランザクション:")
    for tx in transactions:
        print(f"    {tx}")
    
    # ステップ3: 候補経路の生成
    print("\n[ステップ3] 候補経路の生成")
    print("  各トランザクションに対して3つの候補経路をDijkstra法で生成")
    
    start_time = time.time()
    route_candidates = route_finder.find_all_route_candidates(transactions)
    route_gen_time = time.time() - start_time
    
    print(f"  経路生成時間: {route_gen_time:.2f}秒")
    
    total_routes = sum(len(routes) for routes in route_candidates.values())
    print(f"  総候補経路数: {total_routes}")
    
    for tx in transactions:
        tx_id = tx.transaction_id
        if tx_id in route_candidates:
            print(f"\n  Transaction {tx_id}:")
            for idx, route in enumerate(route_candidates[tx_id]):
                route_info = route_finder.get_route_info(route)
                print(f"    候補{idx+1}: ホップ数={route_info['num_hops']}, "
                      f"手数料={route_info['total_fee']:.4f}")
    
    # ステップ4: 最適化の実行
    print("\n[ステップ4] 量子アニーリングによる最適化")
    print("  論文の設定: α=2, β=平均金額²×100")
    
    import datetime
    
    optimizer = RouteOptimizer(
        ln_graph,
        use_cloud_solver=True,
        time_limit=datetime.timedelta(seconds=10)  # 論文: 10秒
    )
    
    result = optimizer.optimize(
        transactions,
        alpha=2.0,
        beta=None,  # 自動計算（平均金額²×100）
        num_route_candidates=3
    )
    
    # ステップ5: 結果の詳細表示
    print("\n[ステップ5] 結果の分析")
    
    optimizer.print_result(result, transactions)
    
    # 論文との比較
    print("\n[論文との比較]")
    print(f"  論文の結果:")
    print(f"    - 実行時間: 10秒 (通信時間を含む)")
    print(f"    - 要したビット数: 361ビット")
    print(f"    - 制約を満たす解を取得")
    print(f"    - 短い距離の経路を選択")
    
    print(f"\n  本実装の結果:")
    print(f"    - 実行時間: {result.execution_time:.2f}秒")
    print(f"    - 制約充足: {'✓ 満たす' if result.is_feasible else '✗ 満たさない'}")
    print(f"    - 平均ホップ数: {result.statistics['avg_hops']:.2f}")
    print(f"    - 平均手数料: {result.statistics['avg_fee']:.4f}")
    
    # 最終評価
    if result.is_feasible and result.execution_time <= 10:
        print("\n✓ 論文の結果を再現できました！")
    elif result.is_feasible:
        print("\n✓ 制約を満たす解が得られましたが、実行時間が論文より長いです")
    else:
        print("\n⚠️  制約違反があります。パラメータの調整が必要かもしれません")
    
    return result


if __name__ == "__main__":
    try:
        result = main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

