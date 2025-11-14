"""
Route Finder for Lightning Network

Finds candidate routes for transactions using Dijkstra's algorithm.
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict


class Transaction:
    """
    トランザクションを表すクラス
    
    Attributes:
        source (int): 送信元ノード
        target (int): 送信先ノード
        amount (int): 送金額
        transaction_id (int): トランザクションID
    """
    
    def __init__(self, source: int, target: int, amount: int, transaction_id: int):
        self.source = source
        self.target = target
        self.amount = amount
        self.transaction_id = transaction_id
    
    def __repr__(self):
        return f"Transaction(id={self.transaction_id}, {self.source}->{self.target}, amount={self.amount})"


class RouteFinder:
    """
    トランザクションの候補経路を探索するクラス
    
    Dijkstra法を用いて、各トランザクションに対して3つの候補経路を生成する
    """
    
    def __init__(self, graph: nx.Graph, num_route_candidates: int = 3):
        """
        Args:
            graph: Lightning Networkのグラフ
            num_route_candidates: 各トランザクションの候補経路数（デフォルト: 3）
        """
        self.graph = graph
        self.num_route_candidates = num_route_candidates
        self.rng = np.random.default_rng(42)
    
    def generate_transactions(
        self,
        num_transactions: int = 4,
        amount_range: Tuple[int, int] = (200, 600),
        seed: int = 42
    ) -> List[Transaction]:
        """
        ランダムなトランザクションを生成
        
        論文の設定:
        - トランザクション数: 4
        - 金額範囲: 200-600
        
        Args:
            num_transactions: トランザクション数
            amount_range: 金額の範囲
            seed: 乱数シード
        
        Returns:
            List[Transaction]: 生成されたトランザクションのリスト
        """
        rng = np.random.default_rng(seed)
        nodes = list(self.graph.nodes())
        transactions = []
        
        for i in range(num_transactions):
            # 送信元と送信先をランダムに選択（異なるノード）
            source, target = rng.choice(nodes, size=2, replace=False)
            
            # 金額をランダムに生成
            amount = rng.integers(amount_range[0], amount_range[1] + 1)
            
            transactions.append(Transaction(source, target, amount, i))
        
        return transactions
    
    def find_route_candidates(
        self,
        transaction: Transaction
    ) -> List[List[int]]:
        """
        1つのトランザクションに対して候補経路を探索
        
        論文では「手数料に平均0.1、標準偏差1の乱数を掛け合わせたものを
        手数料の重みとしたグラフにおける最短経路をダイクストラ法によって求める」
        
        Args:
            transaction: トランザクション
        
        Returns:
            List[List[int]]: 候補経路のリスト（各経路はノードのリスト）
        """
        routes = []
        
        # グラフのコピーを作成（重みを変更するため）
        G_temp = self.graph.copy()
        
        for attempt in range(self.num_route_candidates):
            try:
                # 経路を探索
                if attempt == 0:
                    # 1つ目の候補: 標準的な最短経路
                    path = self._find_shortest_path(G_temp, transaction)
                else:
                    # 2つ目以降: 重みにランダム性を加えて多様性を持たせる
                    self._randomize_weights(G_temp, randomness=0.3 * attempt)
                    path = self._find_shortest_path(G_temp, transaction)
                
                if path and len(path) > 1:
                    # 既存の経路と重複しないか確認
                    if path not in routes:
                        routes.append(path)
                
                # 十分な候補が見つかったら終了
                if len(routes) >= self.num_route_candidates:
                    break
                    
            except nx.NetworkXNoPath:
                continue
        
        # 候補が見つからない場合は空リストを返す
        if not routes:
            print(f"警告: Transaction {transaction.transaction_id} の経路が見つかりません")
        
        return routes
    
    def _find_shortest_path(
        self,
        G: nx.Graph,
        transaction: Transaction
    ) -> List[int]:
        """
        Dijkstra法で最短経路を探索
        
        Args:
            G: グラフ
            transaction: トランザクション
        
        Returns:
            List[int]: ノードのリスト（経路）
        """
        try:
            path = nx.dijkstra_path(
                G,
                transaction.source,
                transaction.target,
                weight='weight'
            )
            return path
        except nx.NetworkXNoPath:
            raise
    
    def _randomize_weights(self, G: nx.Graph, randomness: float = 0.2):
        """
        グラフの重み（手数料）にランダム性を加える
        
        Args:
            G: グラフ
            randomness: ランダム性の強さ（0-1）
        """
        for u, v in G.edges():
            original_weight = G[u][v]['fee']
            # ランダムな乱数を加える
            multiplier = 1.0 + self.rng.normal(0, randomness)
            multiplier = max(0.1, multiplier)  # 負にならないように
            G[u][v]['weight'] = original_weight * multiplier
    
    def find_all_route_candidates(
        self,
        transactions: List[Transaction]
    ) -> Dict[int, List[List[int]]]:
        """
        すべてのトランザクションに対して候補経路を探索
        
        Args:
            transactions: トランザクションのリスト
        
        Returns:
            Dict: {transaction_id: [route1, route2, route3]}
        """
        all_routes = {}
        
        for transaction in transactions:
            routes = self.find_route_candidates(transaction)
            all_routes[transaction.transaction_id] = routes
        
        return all_routes
    
    def get_route_info(self, route: List[int]) -> Dict:
        """
        経路の情報を取得
        
        Args:
            route: 経路（ノードのリスト）
        
        Returns:
            Dict: 経路の情報（距離、総手数料、使用チャネル等）
        """
        if len(route) < 2:
            return {
                'num_hops': 0,
                'total_fee': 0,
                'channels': [],
                'capacities': []
            }
        
        num_hops = len(route) - 1
        total_fee = 0
        channels = []
        capacities = []
        
        for i in range(num_hops):
            u, v = route[i], route[i + 1]
            channels.append((u, v))
            
            if self.graph.has_edge(u, v):
                total_fee += self.graph[u][v]['fee']
                capacities.append(self.graph[u][v]['capacity'])
            else:
                # エッジが存在しない場合（エラー）
                print(f"警告: エッジ ({u}, {v}) が存在しません")
        
        return {
            'num_hops': num_hops,
            'total_fee': total_fee,
            'channels': channels,
            'capacities': capacities,
            'avg_capacity': np.mean(capacities) if capacities else 0
        }

