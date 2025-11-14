"""
Lightning Network Graph Generator

Generates a graph structure that simulates the Lightning Network topology.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple


class LightningNetworkGraph:
    """
    Lightning Network のグラフ構造を生成するクラス
    
    Attributes:
        num_nodes (int): ノード数
        num_channels (int): チャネル数
        capacity_range (Tuple[int, int]): チャネルのキャパシティ範囲
        graph (nx.Graph): NetworkXグラフオブジェクト
    """
    
    def __init__(
        self,
        num_nodes: int = 2000,
        num_channels: int = 20000,
        capacity_range: Tuple[int, int] = (200, 900),
        seed: int = 42
    ):
        """
        Args:
            num_nodes: ノード数（デフォルト: 2000）
            num_channels: チャネル数（デフォルト: 20000）
            capacity_range: チャネルのキャパシティ範囲（デフォルト: (200, 900)）
            seed: 乱数シード
        """
        self.num_nodes = num_nodes
        self.num_channels = num_channels
        self.capacity_range = capacity_range
        self.seed = seed
        self.graph = None
        self.rng = np.random.default_rng(seed)
        
    def generate(self) -> nx.Graph:
        """
        Lightning Network を模したグラフを生成
        
        論文の設定:
        - ノード数: 2000
        - チャネル数: 20000
        - 各ノードに15-30程度のチャネルがランダムに配置
        - キャパシティ: 200-900の範囲
        
        Returns:
            nx.Graph: 生成されたグラフ
        """
        # グラフの基本構造を生成（スケールフリーネットワークを使用）
        # Lightning Networkはスケールフリー特性を持つ
        self.graph = self._create_scale_free_graph()
        
        # チャネルの属性を設定
        self._set_channel_attributes()
        
        return self.graph
    
    def _create_scale_free_graph(self) -> nx.Graph:
        """
        スケールフリーネットワークを生成
        
        Barabási-Albertモデルを使用して、各ノードに平均15-30のチャネルを配置
        """
        # 平均接続数を計算
        avg_degree = self.num_channels * 2 // self.num_nodes
        m = max(1, avg_degree // 2)  # 新しいノードが接続するエッジ数
        
        # Barabási-Albertグラフを生成
        G = nx.barabasi_albert_graph(
            self.num_nodes,
            m,
            seed=self.seed
        )
        
        # エッジ数を調整（必要に応じて）
        current_edges = G.number_of_edges()
        target_edges = self.num_channels
        
        if current_edges < target_edges:
            # 不足分のエッジを追加
            self._add_random_edges(G, target_edges - current_edges)
        elif current_edges > target_edges:
            # 過剰分のエッジを削除
            self._remove_random_edges(G, current_edges - target_edges)
        
        return G
    
    def _add_random_edges(self, G: nx.Graph, num_edges: int):
        """ランダムにエッジを追加"""
        nodes = list(G.nodes())
        added = 0
        attempts = 0
        max_attempts = num_edges * 10
        
        while added < num_edges and attempts < max_attempts:
            u, v = self.rng.choice(nodes, size=2, replace=False)
            if not G.has_edge(u, v):
                G.add_edge(u, v)
                added += 1
            attempts += 1
    
    def _remove_random_edges(self, G: nx.Graph, num_edges: int):
        """ランダムにエッジを削除（連結性を保ちながら）"""
        edges = list(G.edges())
        removed = 0
        
        # エッジをシャッフル
        self.rng.shuffle(edges)
        
        for edge in edges:
            if removed >= num_edges:
                break
            
            # エッジを削除しても連結性が保たれるか確認
            G.remove_edge(*edge)
            if nx.is_connected(G):
                removed += 1
            else:
                # 連結性が失われる場合は戻す
                G.add_edge(*edge)
    
    def _set_channel_attributes(self):
        """チャネルの属性（キャパシティ、手数料）を設定"""
        for u, v in self.graph.edges():
            # キャパシティをランダムに設定
            capacity = self.rng.integers(
                self.capacity_range[0],
                self.capacity_range[1] + 1
            )
            
            # 手数料を設定（平均0.1、標準偏差1の乱数）
            # 論文では「チャネルの手数料に平均0.1、標準偏差1の乱数を掛け合わせた」
            base_fee = 0.1
            fee_multiplier = max(0.01, self.rng.normal(1.0, 1.0))
            fee = base_fee * fee_multiplier
            
            # 属性を設定
            self.graph[u][v]['capacity'] = capacity
            self.graph[u][v]['fee'] = fee
            self.graph[u][v]['weight'] = fee  # Dijkstra法で使用
    
    def get_statistics(self) -> Dict[str, float]:
        """
        グラフの統計情報を取得
        
        Returns:
            Dict: 統計情報（ノード数、エッジ数、平均次数、等）
        """
        if self.graph is None:
            raise ValueError("グラフが生成されていません。generate()を先に実行してください。")
        
        degrees = [d for _, d in self.graph.degree()]
        capacities = [self.graph[u][v]['capacity'] for u, v in self.graph.edges()]
        fees = [self.graph[u][v]['fee'] for u, v in self.graph.edges()]
        
        return {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'avg_degree': np.mean(degrees),
            'min_degree': np.min(degrees),
            'max_degree': np.max(degrees),
            'avg_capacity': np.mean(capacities),
            'min_capacity': np.min(capacities),
            'max_capacity': np.max(capacities),
            'avg_fee': np.mean(fees),
            'is_connected': nx.is_connected(self.graph),
        }
    
    def save_graph(self, filepath: str):
        """グラフをファイルに保存"""
        if self.graph is None:
            raise ValueError("グラフが生成されていません。")
        
        nx.write_gpickle(self.graph, filepath)
    
    def load_graph(self, filepath: str):
        """グラフをファイルから読み込み"""
        self.graph = nx.read_gpickle(filepath)
        return self.graph

