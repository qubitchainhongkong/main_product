#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic Example: Lightning Network Route Optimization

This example demonstrates the basic usage of the Lightning Network
route optimization using quantum annealing.
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph_generator import LightningNetworkGraph
from src.route_finder import RouteFinder
from src.optimizer import RouteOptimizer


def main():
    """メイン関数"""
    
    print("=" * 70)
    print("Lightning Network Route Optimization - Basic Example")
    print("=" * 70)
    
    # ステップ1: グラフの生成
    print("\n[ステップ1] Lightning Network グラフの生成")
    
    # 論文の設定に基づく（小規模版for demo）
    ln_graph = LightningNetworkGraph(
        num_nodes=100,      # デモ用に小規模化 (論文: 2000)
        num_channels=500,   # デモ用に小規模化 (論文: 20000)
        capacity_range=(200, 900),
        seed=42
    )
    
    graph = ln_graph.generate()
    stats = ln_graph.get_statistics()
    
    print(f"  ノード数: {stats['num_nodes']}")
    print(f"  チャネル数: {stats['num_edges']}")
    print(f"  平均次数: {stats['avg_degree']:.2f}")
    print(f"  平均キャパシティ: {stats['avg_capacity']:.2f}")
    print(f"  連結性: {'✓ 連結' if stats['is_connected'] else '✗ 非連結'}")
    
    # ステップ2: トランザクションの生成
    print("\n[ステップ2] トランザクションの生成")
    
    route_finder = RouteFinder(graph, num_route_candidates=3)
    transactions = route_finder.generate_transactions(
        num_transactions=4,  # 論文の設定
        amount_range=(200, 600),
        seed=42
    )
    
    print(f"  トランザクション数: {len(transactions)}")
    for tx in transactions:
        print(f"    {tx}")
    
    # ステップ3: 最適化の実行
    print("\n[ステップ3] 経路の最適化")
    
    optimizer = RouteOptimizer(
        ln_graph,
        use_cloud_solver=True
    )
    
    result = optimizer.optimize(
        transactions,
        alpha=2.0,  # 論文の設定
        beta=None,  # 自動計算
        num_route_candidates=3
    )
    
    # ステップ4: 結果の表示
    optimizer.print_result(result, transactions)
    
    # 結果のサマリー
    if result.is_feasible:
        print("\n✓ 最適化に成功しました！")
        print(f"  全トランザクションの経路が見つかりました")
        print(f"  総手数料: {result.statistics['total_fee']:.4f}")
        print(f"  総ホップ数: {result.statistics['total_hops']}")
    else:
        print("\n⚠️  最適化は完了しましたが、制約違反があります")
    
    return result


if __name__ == "__main__":
    result = main()

