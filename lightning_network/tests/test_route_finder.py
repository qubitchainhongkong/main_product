"""
Unit tests for route_finder.py
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.graph_generator import LightningNetworkGraph
from src.route_finder import RouteFinder, Transaction


def test_transaction_creation():
    """Transactionクラスのテスト"""
    tx = Transaction(source=0, target=10, amount=500, transaction_id=1)
    
    assert tx.source == 0
    assert tx.target == 10
    assert tx.amount == 500
    assert tx.transaction_id == 1


def test_generate_transactions():
    """トランザクション生成のテスト"""
    ln_graph = LightningNetworkGraph(num_nodes=50, num_channels=200, seed=42)
    graph = ln_graph.generate()
    
    route_finder = RouteFinder(graph)
    transactions = route_finder.generate_transactions(num_transactions=5)
    
    assert len(transactions) == 5
    
    for tx in transactions:
        assert isinstance(tx, Transaction)
        assert tx.source != tx.target
        assert 200 <= tx.amount <= 600


def test_route_finding():
    """経路探索のテスト"""
    ln_graph = LightningNetworkGraph(num_nodes=30, num_channels=100, seed=42)
    graph = ln_graph.generate()
    
    route_finder = RouteFinder(graph, num_route_candidates=3)
    transactions = route_finder.generate_transactions(num_transactions=2)
    
    route_candidates = route_finder.find_all_route_candidates(transactions)
    
    assert len(route_candidates) > 0
    
    for tx_id, routes in route_candidates.items():
        # 各トランザクションに少なくとも1つの経路がある
        assert len(routes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

