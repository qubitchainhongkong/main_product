"""
Hamiltonian Builder for Lightning Network Route Optimization

Builds the Hamiltonian (objective function) for quantum annealing.
"""

import numpy as np
import networkx as nx
from typing import List, Dict, Tuple
import amplify
from amplify import VariableGenerator

from .route_finder import Transaction


class HamiltonianBuilder:
    """
    ハミルトニアン（目的関数）を構築するクラス
    
    論文に基づく3つのハミルトニアン:
    1. キャパシティコスト: チャネルのキャパシティ制約
    2. ルート制限: 各トランザクションは1つの経路のみ選択
    3. 距離コスト: 経路を短くする（手数料を最小化）
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        transactions: List[Transaction],
        route_candidates: Dict[int, List[List[int]]],
        alpha: float = 2.0,
        beta: float = None
    ):
        """
        Args:
            graph: Lightning Networkのグラフ
            transactions: トランザクションのリスト
            route_candidates: 各トランザクションの候補経路
            alpha: ルート制限の重み（デフォルト: 2.0）
            beta: 距離コストの重み（デフォルト: 自動計算）
        """
        self.graph = graph
        self.transactions = transactions
        self.route_candidates = route_candidates
        self.alpha = alpha
        
        # β の計算（論文の設定）
        if beta is None:
            avg_amount = np.mean([t.amount for t in transactions])
            self.beta = (avg_amount ** 2) * 100
        else:
            self.beta = beta
        
        self.num_transactions = len(transactions)
        self.num_route_candidates = max(
            len(routes) for routes in route_candidates.values()
        )
        
        # 二値変数の生成
        self.gen = VariableGenerator()
        self.x = None  # トランザクション×候補経路の二値行列
        
    def create_variables(self) -> amplify.BinaryPolyArray:
        """
        二値変数を作成
        
        x[i][j]: トランザクションiが経路jを使用する場合1、そうでない場合0
        
        Returns:
            amplify.BinaryPolyArray: 二値変数の配列
        """
        # トランザクション数×候補経路数の二値配列
        self.x = self.gen.array("Binary", shape=(self.num_transactions, self.num_route_candidates))
        return self.x
    
    def build_capacity_constraint_hamiltonian(self) -> amplify.Poly:
        """
        キャパシティコストのハミルトニアンを構築
        
        全てのチャネルに対して、そのチャネルを通る容量がキャパシティよりも
        大きいとペナルティが発生する。
        
        論文では対数エンコーディングを使用しているが、ここでは簡略化のため
        線形制約を使用。
        
        Returns:
            amplify.Poly: キャパシティ制約のハミルトニアン
        """
        H_capacity = 0
        
        # 各チャネルについて
        for u, v in self.graph.edges():
            channel_capacity = self.graph[u][v]['capacity']
            
            # このチャネルを使用するトランザクションの総量を計算
            channel_usage = 0
            
            for tx in self.transactions:
                tx_id = tx.transaction_id
                amount = tx.amount
                
                # この経路がチャネル(u,v)を使用するか確認
                if tx_id in self.route_candidates:
                    for route_idx, route in enumerate(self.route_candidates[tx_id]):
                        if route_idx < self.num_route_candidates:
                            # 経路がチャネル(u,v)または(v,u)を含むか確認
                            uses_channel = self._route_uses_channel(route, u, v)
                            
                            if uses_channel:
                                channel_usage += amount * self.x[tx_id][route_idx]
            
            # キャパシティを超える場合のペナルティ
            # (channel_usage - capacity)^2 の形でペナルティを課す
            if channel_usage != 0:  # 最適化のため、使用されないチャネルはスキップ
                penalty = (channel_usage - channel_capacity) ** 2
                H_capacity += penalty
        
        return H_capacity
    
    def build_route_constraint_hamiltonian(self) -> amplify.Poly:
        """
        ルート制限のハミルトニアンを構築
        
        各トランザクションでは1つのルートのみが選択される。
        
        制約: Σ_j x[i][j] = 1  (各トランザクションiについて)
        
        Returns:
            amplify.Poly: ルート制限のハミルトニアン
        """
        H_route = 0
        
        for tx in self.transactions:
            tx_id = tx.transaction_id
            
            if tx_id in self.route_candidates:
                # このトランザクションで利用可能な経路数
                num_routes = min(
                    len(self.route_candidates[tx_id]),
                    self.num_route_candidates
                )
                
                if num_routes > 0:
                    # Σ_j x[i][j] = 1 の制約
                    route_sum = sum(self.x[tx_id][j] for j in range(num_routes))
                    H_route += (route_sum - 1) ** 2
        
        return self.alpha * H_route
    
    def build_distance_cost_hamiltonian(self) -> amplify.Poly:
        """
        距離コストのハミルトニアンを構築
        
        経路の距離（経由するチャネル数）を最小化する。
        手数料を少なくすることを目的とする。
        
        Returns:
            amplify.Poly: 距離コストのハミルトニアン
        """
        H_distance = 0
        
        for tx in self.transactions:
            tx_id = tx.transaction_id
            
            if tx_id in self.route_candidates:
                for route_idx, route in enumerate(self.route_candidates[tx_id]):
                    if route_idx < self.num_route_candidates:
                        # 経路の距離（ホップ数 = チャネル数）
                        distance = len(route) - 1  # ノード数 - 1 = チャネル数
                        
                        # この経路が選択された場合の距離コスト
                        H_distance += distance * self.x[tx_id][route_idx]
        
        return self.beta * H_distance
    
    def build_total_hamiltonian(self) -> Tuple[amplify.Poly, Dict[str, amplify.Poly]]:
        """
        総合的なハミルトニアンを構築
        
        H_total = H_capacity + H_route + H_distance
        
        Returns:
            Tuple: (総ハミルトニアン, 各ハミルトニアンの辞書)
        """
        # 変数の作成
        if self.x is None:
            self.create_variables()
        
        # 各ハミルトニアンの構築
        H_capacity = self.build_capacity_constraint_hamiltonian()
        H_route = self.build_route_constraint_hamiltonian()
        H_distance = self.build_distance_cost_hamiltonian()
        
        # 総合ハミルトニアン
        H_total = H_capacity + H_route + H_distance
        
        hamiltonians = {
            'capacity': H_capacity,
            'route': H_route,
            'distance': H_distance,
            'total': H_total
        }
        
        return H_total, hamiltonians
    
    def _route_uses_channel(self, route: List[int], u: int, v: int) -> bool:
        """
        経路がチャネル(u,v)または(v,u)を使用するか確認
        
        Args:
            route: 経路（ノードのリスト）
            u, v: チャネルの両端ノード
        
        Returns:
            bool: 使用する場合True
        """
        if len(route) < 2:
            return False
        
        for i in range(len(route) - 1):
            node1, node2 = route[i], route[i + 1]
            # 無向グラフなので両方向をチェック
            if (node1 == u and node2 == v) or (node1 == v and node2 == u):
                return True
        
        return False
    
    def get_variable_info(self) -> Dict:
        """
        変数の情報を取得
        
        Returns:
            Dict: 変数の情報
        """
        total_variables = self.num_transactions * self.num_route_candidates
        
        # 実際に使用される変数の数（候補経路が存在するもののみ）
        used_variables = 0
        for tx in self.transactions:
            tx_id = tx.transaction_id
            if tx_id in self.route_candidates:
                used_variables += len(self.route_candidates[tx_id])
        
        return {
            'num_transactions': self.num_transactions,
            'num_route_candidates': self.num_route_candidates,
            'total_variables': total_variables,
            'used_variables': used_variables,
            'alpha': self.alpha,
            'beta': self.beta
        }

