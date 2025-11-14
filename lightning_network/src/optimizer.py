"""
Route Optimizer for Lightning Network

Optimizes transaction routes using quantum annealing (Fixstars Amplify).
"""

import os
import datetime
import numpy as np
from typing import List, Dict, Tuple, Optional
import amplify
from dotenv import load_dotenv

from .graph_generator import LightningNetworkGraph
from .route_finder import Transaction, RouteFinder
from .hamiltonian import HamiltonianBuilder

# .envファイルを読み込む
load_dotenv()


class OptimizationResult:
    """最適化結果を格納するクラス"""
    
    def __init__(
        self,
        selected_routes: Dict[int, int],
        route_paths: Dict[int, List[int]],
        objective_value: float,
        execution_time: float,
        is_feasible: bool,
        statistics: Dict
    ):
        self.selected_routes = selected_routes  # {tx_id: route_index}
        self.route_paths = route_paths  # {tx_id: [node_path]}
        self.objective_value = objective_value
        self.execution_time = execution_time
        self.is_feasible = is_feasible
        self.statistics = statistics
    
    def __repr__(self):
        return (f"OptimizationResult(feasible={self.is_feasible}, "
                f"objective={self.objective_value:.2f}, "
                f"time={self.execution_time:.2f}s)")


class RouteOptimizer:
    """
    Lightning Network のルート最適化を実行するクラス
    
    量子アニーリング（Fixstars Amplify）を使用して最適な経路を選択する
    """
    
    def __init__(
        self,
        graph: LightningNetworkGraph,
        use_cloud_solver: bool = True,
        time_limit: datetime.timedelta = datetime.timedelta(seconds=10)
    ):
        """
        Args:
            graph: Lightning Networkのグラフ
            use_cloud_solver: クラウドソルバーを使用するか（デフォルト: True）
            time_limit: ソルバーの実行時間制限
        """
        self.ln_graph = graph
        self.graph = graph.graph
        self.use_cloud_solver = use_cloud_solver
        self.time_limit = time_limit
        
        # ソルバークライアントの初期化
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """
        Amplify ソルバークライアントを初期化
        
        Returns:
            初期化されたクライアント
        """
        if self.use_cloud_solver:
            # Fixstars Amplify AE (クラウド)
            client = amplify.AmplifyAEClient()
            client.parameters.time_limit_ms = self.time_limit
            
            # APIトークンの設定
            amplify_token = os.getenv("AMPLIFY_TOKEN")
            if amplify_token and amplify_token != "your_api_token_here":
                client.token = amplify_token
                print("✓ Amplify AE クライアント初期化完了（APIトークン設定済み）")
            else:
                print("⚠️  APIトークンが未設定です。.envファイルを確認してください。")
        else:
            # ローカルソルバー（Fixstars Amplify Annealing Engine など）
            # ここでは簡易的なソルバーを使用
            client = amplify.AmplifyAEClient()
            print("⚠️  ローカルソルバーは未実装です。クラウドソルバーを使用してください。")
        
        return client
    
    def optimize(
        self,
        transactions: List[Transaction],
        alpha: float = 2.0,
        beta: Optional[float] = None,
        num_route_candidates: int = 3
    ) -> OptimizationResult:
        """
        トランザクションの経路を最適化
        
        Args:
            transactions: トランザクションのリスト
            alpha: ルート制限の重み
            beta: 距離コストの重み（Noneの場合は自動計算）
            num_route_candidates: 各トランザクションの候補経路数
        
        Returns:
            OptimizationResult: 最適化結果
        """
        print("\n" + "="*70)
        print("Lightning Network Route Optimization")
        print("="*70)
        
        # ステップ1: 候補経路の生成
        print("\n[ステップ1] 候補経路の生成")
        route_finder = RouteFinder(self.graph, num_route_candidates)
        route_candidates = route_finder.find_all_route_candidates(transactions)
        
        # 統計情報の表示
        total_routes = sum(len(routes) for routes in route_candidates.values())
        print(f"  トランザクション数: {len(transactions)}")
        print(f"  生成された候補経路数: {total_routes}")
        
        # ステップ2: ハミルトニアンの構築
        print("\n[ステップ2] ハミルトニアンの構築")
        hamiltonian_builder = HamiltonianBuilder(
            self.graph,
            transactions,
            route_candidates,
            alpha=alpha,
            beta=beta
        )
        
        H_total, hamiltonians = hamiltonian_builder.build_total_hamiltonian()
        var_info = hamiltonian_builder.get_variable_info()
        
        print(f"  使用変数数: {var_info['used_variables']}")
        print(f"  α (ルート制限): {var_info['alpha']}")
        print(f"  β (距離コスト): {var_info['beta']:.2f}")
        
        # ステップ3: 最適化の実行
        print("\n[ステップ3] 最適化の実行")
        print(f"  ソルバー: Fixstars Amplify AE")
        print(f"  時間制限: {self.time_limit}")
        
        import time
        start_time = time.time()
        
        try:
            # 最適化モデルの作成
            model = amplify.Model(H_total)
            
            # ソルバーの実行
            result = amplify.solve(model, self.client)
            
            execution_time = time.time() - start_time
            
            if len(result) == 0:
                print("  ⚠️  実行可能な解が見つかりませんでした")
                return self._create_empty_result(execution_time)
            
            # 結果の解析
            print(f"  ✓ 最適化完了 (実行時間: {execution_time:.2f}秒)")
            
            optimization_result = self._parse_result(
                result,
                hamiltonian_builder,
                transactions,
                route_candidates,
                execution_time
            )
            
            return optimization_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ✗ エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result(execution_time)
    
    def _parse_result(
        self,
        result: amplify.Result,
        hamiltonian_builder: HamiltonianBuilder,
        transactions: List[Transaction],
        route_candidates: Dict[int, List[List[int]]],
        execution_time: float
    ) -> OptimizationResult:
        """
        最適化結果を解析
        
        Args:
            result: Amplifyの最適化結果
            hamiltonian_builder: ハミルトニアンビルダー
            transactions: トランザクションのリスト
            route_candidates: 候補経路
            execution_time: 実行時間
        
        Returns:
            OptimizationResult: 解析された結果
        """
        # 最良解を取得
        best_solution = result.best
        x = hamiltonian_builder.x
        
        # 選択された経路を取得
        selected_routes = {}
        route_paths = {}
        
        for tx in transactions:
            tx_id = tx.transaction_id
            
            if tx_id in route_candidates:
                # x[tx_id][route_idx] が 1 となる経路を探す
                for route_idx, route in enumerate(route_candidates[tx_id]):
                    if route_idx < hamiltonian_builder.num_route_candidates:
                        value = x[tx_id][route_idx].evaluate(best_solution.values)
                        
                        if value > 0.5:  # 二値変数なので0.5以上を1とみなす
                            selected_routes[tx_id] = route_idx
                            route_paths[tx_id] = route
                            break
        
        # 統計情報の計算
        statistics = self._calculate_statistics(
            transactions,
            selected_routes,
            route_paths
        )
        
        # 実行可能性のチェック
        is_feasible = self._check_feasibility(
            transactions,
            route_paths
        )
        
        return OptimizationResult(
            selected_routes=selected_routes,
            route_paths=route_paths,
            objective_value=best_solution.objective,
            execution_time=execution_time,
            is_feasible=is_feasible,
            statistics=statistics
        )
    
    def _calculate_statistics(
        self,
        transactions: List[Transaction],
        selected_routes: Dict[int, int],
        route_paths: Dict[int, List[int]]
    ) -> Dict:
        """統計情報を計算"""
        total_hops = 0
        total_fee = 0
        
        for tx in transactions:
            tx_id = tx.transaction_id
            
            if tx_id in route_paths:
                route = route_paths[tx_id]
                num_hops = len(route) - 1
                total_hops += num_hops
                
                # 手数料の計算
                for i in range(num_hops):
                    u, v = route[i], route[i + 1]
                    if self.graph.has_edge(u, v):
                        total_fee += self.graph[u][v]['fee']
        
        return {
            'num_selected_routes': len(selected_routes),
            'total_hops': total_hops,
            'avg_hops': total_hops / len(transactions) if transactions else 0,
            'total_fee': total_fee,
            'avg_fee': total_fee / len(transactions) if transactions else 0
        }
    
    def _check_feasibility(
        self,
        transactions: List[Transaction],
        route_paths: Dict[int, List[int]]
    ) -> bool:
        """
        解の実行可能性をチェック
        
        1. 全てのトランザクションに経路が割り当てられているか
        2. チャネルのキャパシティ制約を満たしているか
        """
        # 全てのトランザクションに経路が割り当てられているか
        if len(route_paths) != len(transactions):
            return False
        
        # チャネルの使用量を計算
        channel_usage = {}
        
        for tx in transactions:
            tx_id = tx.transaction_id
            
            if tx_id in route_paths:
                route = route_paths[tx_id]
                
                for i in range(len(route) - 1):
                    u, v = route[i], route[i + 1]
                    
                    # エッジのキーを正規化（無向グラフ）
                    edge = tuple(sorted([u, v]))
                    
                    if edge not in channel_usage:
                        channel_usage[edge] = 0
                    
                    channel_usage[edge] += tx.amount
        
        # キャパシティ制約のチェック
        for edge, usage in channel_usage.items():
            u, v = edge
            if self.graph.has_edge(u, v):
                capacity = self.graph[u][v]['capacity']
                if usage > capacity:
                    return False
        
        return True
    
    def _create_empty_result(self, execution_time: float) -> OptimizationResult:
        """空の結果を作成（エラー時）"""
        return OptimizationResult(
            selected_routes={},
            route_paths={},
            objective_value=float('inf'),
            execution_time=execution_time,
            is_feasible=False,
            statistics={
                'num_selected_routes': 0,
                'total_hops': 0,
                'avg_hops': 0,
                'total_fee': 0,
                'avg_fee': 0
            }
        )
    
    def print_result(self, result: OptimizationResult, transactions: List[Transaction]):
        """結果を見やすく表示"""
        print("\n" + "="*70)
        print("最適化結果")
        print("="*70)
        
        print(f"\n実行時間: {result.execution_time:.2f}秒")
        print(f"目的関数値: {result.objective_value:.2f}")
        print(f"実行可能性: {'✓ 制約を満たしています' if result.is_feasible else '✗ 制約違反があります'}")
        
        print(f"\n統計情報:")
        print(f"  選択された経路数: {result.statistics['num_selected_routes']}")
        print(f"  総ホップ数: {result.statistics['total_hops']}")
        print(f"  平均ホップ数: {result.statistics['avg_hops']:.2f}")
        print(f"  総手数料: {result.statistics['total_fee']:.4f}")
        print(f"  平均手数料: {result.statistics['avg_fee']:.4f}")
        
        print(f"\n選択された経路:")
        for tx in transactions:
            tx_id = tx.transaction_id
            if tx_id in result.route_paths:
                route = result.route_paths[tx_id]
                route_idx = result.selected_routes[tx_id]
                print(f"  Transaction {tx_id} ({tx.source} -> {tx.target}, {tx.amount}):")
                print(f"    経路候補 {route_idx}: {' -> '.join(map(str, route))}")
                print(f"    ホップ数: {len(route) - 1}")
            else:
                print(f"  Transaction {tx_id}: 経路が選択されていません")
        
        print("="*70)

