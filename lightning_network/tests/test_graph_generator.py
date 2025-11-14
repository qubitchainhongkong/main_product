"""
Unit tests for graph_generator.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph_generator import LightningNetworkGraph


def test_graph_generation():
    """グラフ生成のテスト"""
    ln_graph = LightningNetworkGraph(
        num_nodes=50,
        num_channels=200,
        seed=42
    )
    
    graph = ln_graph.generate()
    
    # 基本的なチェック
    assert graph is not None
    assert graph.number_of_nodes() == 50
    # チャネル数は完全に一致しない場合があるが、近い値であることを確認
    assert abs(graph.number_of_edges() - 200) < 50


def test_graph_attributes():
    """グラフの属性テスト"""
    ln_graph = LightningNetworkGraph(
        num_nodes=20,
        num_channels=50,
        capacity_range=(100, 500),
        seed=42
    )
    
    graph = ln_graph.generate()
    
    # エッジ属性のチェック
    for u, v in graph.edges():
        assert 'capacity' in graph[u][v]
        assert 'fee' in graph[u][v]
        assert 'weight' in graph[u][v]
        
        capacity = graph[u][v]['capacity']
        assert 100 <= capacity <= 500


def test_graph_statistics():
    """統計情報取得のテスト"""
    ln_graph = LightningNetworkGraph(num_nodes=30, num_channels=100, seed=42)
    graph = ln_graph.generate()
    
    stats = ln_graph.get_statistics()
    
    assert 'num_nodes' in stats
    assert 'num_edges' in stats
    assert 'avg_degree' in stats
    assert 'is_connected' in stats
    
    assert stats['num_nodes'] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

