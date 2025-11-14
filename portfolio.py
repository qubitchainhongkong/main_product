#!/usr/bin/env python
# coding: utf-8

# # ポートフォリオ最適化
# 
# このチュートリアルにおいて、ポートフォリオとは株式や債券などの金融商品の組み合わせのことです。このような金融商品は銀行預金とは異なり、将来の受取金額が確定していないリスク資産であり、収益率も不確定です。リスク資産への投資においては、適切なポートフォリオを組み、互いに大きな相関のない複数資産へ分散投資することが推奨されます。こうすることで、保有するある資産の価値が大きく下がった場合においても、その資産の値動きと大きな相関を持たない別の資産によってカバーできる可能性があります。
# 
# 一般的に、分散投資におけるリスクとリターンにはトレードオフの関係があります。収益率のバラつきや損失を被るリスクを抑え、リターンを最大化するには、このトレードオフのバランスを適切に反映したポートフォリオを組む必要があります。
# 
# ここでは、Fixstars Amplify を用いて、ポートフォリオを最適化します。最適化にはヒストリカルデータ方式に基づく推計値を用います。ヒストリカルデータ方式とは、過去の値動きデータに基づいて資産の期待収益率やリスクを求める推計方法です。本サンプルプログラムでは、以下の順に従って解説します。
# 
# - [株価データの取得](#1)
# - [最適ポートフォリオ求解のための定式化及びソルバの実装](#2)
# - [最適化の実行と評価](#3)
# - [運用シミュレーション](#4)
# 
# ※本サンプルプログラムは、Fixstars Amplify を利用した最適化アプリケーションのデモンストレーションを目的としています。この情報を基に実際の運用を行う際には、ユーザー自身の責任において実施してください。
# 

# <a id="1"></a>
# 
# ## 株価データの取得
# 
# まず、株価の時系列データを作成します。幾何ブラウン運動に基づいたダミーのシミュレーションデータ (`dummy_stock_price.csv`) を用意しました。シミュレーションにおいては、2023 年から 2024 年前半にかけての NASDAQ インデックスを構成する各銘柄の値動きに対し、利益率、ボラタリティ (リスク)、銘柄間の相関係数の分布をできるだけ一致させるように確率微分方程式のパラメータを決定しています。実データを取得する方法については、このチュートリアルの最後に記述していますので、そちらもあわせて参照してください。
# 
# 以下の `load_stock_prices()` 関数により、シミュレーションデータを読み込むことができます。
# 株価データは `pandas.DataFrame` の形式として表現し、銘柄名 (あるいはティッカー名や銘柄コード) を列、日付を行とし、値には各銘柄ごとに各日の終値を持ちます。たとえば以下の表のように表されます。
# 
# | Date       | 銘柄名 1 | 銘柄名 2 | 銘柄名 3 | ... |
# | ---------- | -------- | -------- | -------- | --- |
# | 2024/03/01 | 123      | 310      | 2102     | ... |
# | 2024/03/04 | 126      | 310      | 2110     | ... |
# | 2024/03/05 | 131      | 313      | 2123     | ... |
# | 2024/03/06 | 127      | 302      | 2140     | ... |
# | ...        | ...      | ...      | ...      | ... |
# 

# In[ ]:


import datetime
import os
import pandas as pd
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


# In[ ]:


def load_stock_prices() -> pd.DataFrame:
    return pd.read_csv(
        "../../../storage/portfolio/dummy_stock_price.csv",
        index_col="Date",
        parse_dates=True,
    )


# <a id="2"></a>
# 
# ## ポートフォリオ最適化の定式化
# 
# ここまでで、株価の時系列データを取得する準備が整いました。ここからは、最適なポートフォリオを実現するための定式化を行います。
# 
# まず、投資する銘柄の候補をピックアップします。このとき金融商品 $0$, 金融商品 $1$, $\ldots$, 金融商品 $n -1$ の $n$ 個の金融商品がピックアップされたとします。投資合計金額に対する金融商品 $i$ への投資比率を $w_i$ (%) とすると、$w_i$ が満たすべき制約条件は、
# 
# $$
# \sum_{i=0}^{n-1} w_i = 100
# $$
# 
# となります。Amplify を使用して最適化を行う都合上、$w_i$ は整数の値をとるとしておきます。また、1 つの金融商品に大きな割合を投資するのはリスクが大きいので、投資合計金額に対する 1 つの金融商品への投資割合を 20% 以下に抑えることにしておきます。
# 
# $$
# 0 \leq w_i \leq 20
# $$
# 
# これら $n$ 個の金融商品の候補からポートフォリオを作成する方法は何通りもありますが、このうちどのようなものが良いポートフォリオとなるかを考えます。期待される収益率が高く、リスクが低いものが良いポートフォリオです。
# 
# まず、期待収益率について、今回は単に株価データ内の任意の $d$ 営業日間について、その期間中に運用した場合の収益率の平均を採用することにします。
# 
# ある銘柄を一定期間運用するとき、運用開始時の価額を $p_{s}$ 、運用終了時の価額を $p_{e}$ とすると、収益率 $r$ は
# 
# $$
# r = (p_{e} - p_{s}) / p_{s}
# $$
# 
# と定義されます。このとき、ポートフォリオ全体の期待収益率 $r_p$ は、金融商品 $i$ の収益率を $r_i$ として
# 
# $$
# r_p = \sum_{i=0}^{n-1} r_i w_i
# $$
# 
# となります。もし他の指標などを用いて期待収益率 (あるいは銘柄の「良さ」) のより良い数値的評価ができるのであれば、そちらを採用しても良いでしょう。
# 
# 次に、リスクについて考えます。分散投資におけるリスクとは、通常、ポートフォリオ全体収益率の分散 $\sigma^2_p$ であり、これは金融商品 $i$ と $j$ の収益率の共分散 $\sigma_{i,j}$ を用いて次のように記述することができます。
# 
# $$
# \sigma_p^2 = \sum_{i=0}^{n-1} \sum_{j=0}^{n-1} w_i w_j \sigma_{i,j}.
# $$
# 
# これで収益率とリスクを定義することができました。収益率 $r_p$ を大きく、リスク $\sigma_p^2$ を小さくするために、以下の平均・分散モデル $f(w_i)$ を目的関数とし、これを最小化するように最適化を行います。
# 
# $$
# f(w_i) = - r_p + \frac{\gamma}{2} \sigma_p^2.
# $$
# 
# ここで、$\gamma$ は収益率とリスクのバランスに関するパラメータです。以下で実装するポートフォリオ最適化では、デフォルト設定として $\gamma=20$ を使用しています。$\gamma$ を大きくするとリスクの低減をより重視することになります。
# 

# ## ポートフォリオ最適化の実装
# 
# 上記の定式化を Amplify SDK を用いて定式化します。最初に、補助関数として収益率を計算する `calculate_return_rates()` 関数を定義します。この関数は、与えられた株価の時系列データ `price` に対して、それぞれの日時から日数 `num_days_operation` だけ運用した場合の収益率を運用開始日・銘柄ごとに計算した二次元配列を返却します。
# 

# In[ ]:


import amplify
import numpy as np


# In[ ]:


def calculate_return_rates(prices: np.ndarray, num_days_operation: int) -> np.ndarray:
    return (prices[num_days_operation:] - prices[:-num_days_operation]) / prices[
        :-num_days_operation
    ]


# 次に、定式化と最適化を行う関数を定義します。
# 
# 以下の `optimize_portfolio()` 関数は、過去の株価の時系列データと運用する日数、およびその他最適化に必要なパラメータを受け取り、最適化されたポートフォリオとその収益率及び分散を返却します。
# 
# この関数のパラメータ `gamma` は 収益率とリスクの低減のうちどちらをより重視するかを表し、大きいほどリスクを小さくしようとする度合いが強くなります。  
# また、`max_w` は 1 銘柄の投資額が全体の投資額に占める割合の最大値を表します。
# 
# (注意: QUBO で定式化する都合により `max_w` を大きくするとマシンに送られる変数の数が多くなるため、最適化問題としては難しくなります)
# 
# `time_limit_ms` は解の精度に関係するパラメータで、Amplify AE の実行時間を表します。詳しくはドキュメントの「[ソルバークライアント](https://amplify.fixstars.com/ja/docs/amplify/v1/clients.html#id2)」を参照してください。
# 
# 実行時間は大規模な (難しい) 問題ほど大きめに取った方が良いですが、ここではチュートリアルなので 5 秒に設定しています。
# 

# In[ ]:


def optimize_portfolio(
    historical_data: pd.DataFrame,
    num_days_operation: int,
    gamma: float = 20,
    max_w: int = 20,
    time_limit_ms: datetime.timedelta = datetime.timedelta(seconds=5),
):
    # 銘柄名のリスト
    stock_names = list(historical_data.columns)

    # 投資比率(%) を表す変数 `w_i` を作成 (0 以上 `max_w` 以下の値を取る整数変数)
    gen = amplify.VariableGenerator()
    w = gen.array("Integer", len(stock_names), bounds=(0, max_w))

    # 制約条件を作成 (w の総和は 100)
    constraint = amplify.equal_to(w.sum(), 100)

    # 目的関数を作成 (収益率の平均を最大化)
    w_ratio = w / 100  # w (単位は %) を実数に変換したもの

    # num_days_operation 営業日運用した場合の銘柄ごとの収益率を計算する
    return_rates = calculate_return_rates(
        historical_data.to_numpy(), num_days_operation
    )

    # ポートフォリオの収益率を定式化
    # それぞれの銘柄の (収益率の平均) * (投資割合) を足し合わせる
    portfolio_return_rate = (w_ratio * np.mean(return_rates, axis=0)).sum()

    # ポートフォリオの共分散 (二次元配列) を計算
    # 配列の i 行 j 列は銘柄 i と銘柄 j の収益率の共分散を表す
    covariance_matrix = np.cov(return_rates, rowvar=False)

    # ポートフォリオのリスクを定式化
    # 全体の収益率の分散を表す w についての二次多項式
    portfolio_variance = w_ratio @ covariance_matrix @ w_ratio  # type: ignore

    # 目的関数の定式化 (gamma はリスク回避度を表すパラメータ)
    objective = -portfolio_return_rate + 0.5 * gamma * portfolio_variance

    # 最適化モデルを作成
    model = amplify.Model(objective, constraint)

    # ソルバークライアントの作成とソルバーの設定
    client = amplify.AmplifyAEClient()
    client.parameters.time_limit_ms = time_limit_ms
    # .envファイルからAPIトークンを読み込む
    amplify_token = os.getenv("AMPLIFY_TOKEN")
    if amplify_token and amplify_token != "your_api_token_here":
        client.token = amplify_token
    # それ以外の場合は、デフォルトのトークンを使用（環境変数などから取得）

    # 最適化を実行
    result = amplify.solve(model, client)

    # 実行結果を解析
    if len(result) == 0:
        raise RuntimeError("No feasible solution found")

    # 全ての銘柄それぞれにいくつ (%) 投資するかを得る
    w_values = w.evaluate(result.best.values)

    # 投資比率が 0 より大きい銘柄のみを抽出してポートフォリオを作成
    portfolio = {
        stock_name: int(w_value)
        for stock_name, w_value in zip(stock_names, w_values)
        if w_value > 0
    }

    # 得られたポートフォリオの収益率とリスクを計算
    return_rate = portfolio_return_rate.evaluate(result.best.values)
    variance = portfolio_variance.evaluate(result.best.values)
    return portfolio, return_rate, variance


# <a id="3"></a>
# 
# ## 最適化の実行と評価
# 
# 実装が完了したので、実際にダミーデータを用いて、最適ポートフォリオを構築します。まず、株価データを表す `pd.DataFrame` を作成します。
# 
# 以下の `stock_prices` には、架空の株価データが入っています。データの期間は 2023 年～ 2024 年の 2 年間 (500 営業日) 分であり、銘柄は色の名前を社名に持つ架空の 100 社分となっています。
# 

# In[ ]:


stock_prices = load_stock_prices()
stock_prices


# 例として、`salmon` 社, `darkslategray` 社, `hotpink` 社の株価の 2 年間の値動きを見てみましょう。
# 

# In[ ]:


import matplotlib.pyplot as plt

plt.plot(stock_prices["salmon"], color="salmon")
plt.plot(stock_prices["darkslategray"], color="darkslategray")
plt.plot(stock_prices["hotpink"], color="hotpink")
plt.show()


# 次に、運用を開始する日時を決定します。運用期間後の検証を行うため、ここでは 2024 年 1 月 1 日に運用を開始したことにします (通常のポートフォリオ最適化では、運用開始日は最適化したポートフォリオで運用を開始する日なので検証は未来に行います)。
# 
# 最適化では運用開始日より過去のデータだけが使用できます。今回は、運用開始日から遡って 1 年分のデータを最適化に使用します。先ほど作成した `stock_prices` から 2023 年の株価データのみを切り出して、株価の時系列データとします。
# 

# In[ ]:


stock_prices_history = stock_prices.loc["2023":"2023"]


# ### ポートフォリオの最適化
# 
# 上記で実装した `optimize_portfolio()` 関数を用い、株価の時系列データに基づいて最適化されたポートフォリオを取得します。運用期間は 20 営業日として収益率を計算します。
# 

# In[ ]:


portfolio, return_rate, variance = optimize_portfolio(
    stock_prices_history, num_days_operation=20
)


# 円グラフを用いてポートフォリオを可視化します。
# 

# In[ ]:


import matplotlib

# カラーマップ
colors = tuple(matplotlib.colormaps.get_cmap("Set3")(range(12)))

# パイチャートの描画
patches, texts, autotexts = plt.pie(  # type: ignore
    list(portfolio.values()),
    labels=list(portfolio.keys()),
    radius=1.5,
    autopct="%.f%%",
    colors=colors,
    labeldistance=0.8,
    wedgeprops={"linewidth": 1.0, "edgecolor": "white"},
    pctdistance=0.5,
)
for text in texts:
    text.set_horizontalalignment("center")
plt.show()


# ### ポートフォリオの評価
# 
# 上記で求めたポートフォリオを用いて、2024 年の任意の 20 営業日で運用した場合の利益率をヒストグラムとしてプロットし、リスクを抑えながらどの程度の利益率が得られるかを確認します。
# 
# 簡単のため、運用開始日および運用終了日の終値と同じ価格で購入・売却を行えるとします。比較対象として、以下の方針で作成したポートフォリオについても同様に評価を行います。
# 
# - 最も平均利益率の高い銘柄に資金をすべて投資する
# - すべての銘柄に均等に投資資金を割り当てる
# 

# In[ ]:


df_future = stock_prices.loc["2024":"2024"]
num_days_operation = 20

historical_return_rates = calculate_return_rates(
    stock_prices_history.to_numpy(), num_days_operation
)
max_profit_stock: str = stock_prices_history.columns[
    historical_return_rates.mean(axis=0).argmax()
]
max_profit_portfolio = {max_profit_stock: 100}
uniform_ratio_portfolio = {stock_name: 1 for stock_name in df_future.columns}


def calculate_portfolio_return_rates(portfolio: dict[str, int]):
    return_rates = calculate_return_rates(df_future.to_numpy(), num_days_operation)
    ratio_array = (
        np.array([portfolio.get(stock_name, 0) for stock_name in df_future.columns])
        / 100
    )  # 各銘柄への投資割合の配列
    return (ratio_array * return_rates).sum(
        axis=1
    )  # 各運用開始日ごとに、ポートフォリオ全体の収益率を計算する


optimized_return_rates = calculate_portfolio_return_rates(portfolio)

max_profit_return_rates = calculate_portfolio_return_rates(max_profit_portfolio)

uniform_return_rates = calculate_portfolio_return_rates(uniform_ratio_portfolio)

print(
    f"optimized:  max return rate = {np.max(optimized_return_rates) * 100:.2f}%, "
    f"mean return rate = {np.mean(optimized_return_rates) * 100:.2f}%, "
    f"min return rate = {np.min(optimized_return_rates) * 100:.2f}%, "
    f"variance = {np.var(optimized_return_rates):.5f}"
)
print(
    f"max profit: max return rate = {np.max(max_profit_return_rates) * 100:.2f}%, "
    f"mean return rate = {np.mean(max_profit_return_rates) * 100:.2f}%, "
    f"min return rate = {np.min(max_profit_return_rates) * 100:.2f}%, "
    f"variance = {np.var(max_profit_return_rates):.5f}"
)
print(
    f"uniform:    max return rate = {np.max(uniform_return_rates) * 100:.2f}%, "
    f"mean return rate = {np.mean(uniform_return_rates) * 100:.2f}%, "
    f"min return rate = {np.min(uniform_return_rates) * 100:.2f}%, "
    f"variance = {np.var(uniform_return_rates):.5f}"
)

bins = np.linspace(-40, 40, 50)
plt.hist(
    optimized_return_rates * 100,
    label="optimized",
    bins=bins,  # type: ignore
    color="royalblue",
    alpha=0.8,
    zorder=3,
)
plt.hist(
    max_profit_return_rates * 100,
    label="max profit",
    bins=bins,  # type: ignore
    color="coral",
    alpha=0.8,
    zorder=1,
)
plt.hist(
    uniform_return_rates * 100,
    label="uniform ratio",
    bins=bins,  # type: ignore
    color="gold",
    alpha=0.8,
    zorder=2,
)
plt.legend()
plt.xlabel("return rate (%)")
plt.show()


# 表示されるヒストグラムが右側に寄っているほど収益率が高くなります。また、ヒストグラムが横に伸びている場合は、収益率のばらつきが大きく、特にマイナスに振れている場合にはリスクが大きいといえます。
# 
# 最適化したポートフォリオは、単一株に投資した場合と比べると平均的な収益率は低いですが、収益率のばらつきは小さくなっていることが分かります。また、全銘柄に均等に投資した場合と比較すると、全体的に収益率が高い銘柄が選ばれていると予想されます。
# 
# リスクの回避度を表すパラメータ $\gamma$ を変更することで、収益率とリスクのトレードオフを運用目的に合わせて調整することができます。`optimize_portfolio()` 関数の引数を変更して試してみてください。
# 

# ## 応用: ポートフォリオ最適化の運用シミュレーションへの適用
# 
# <a id="4"></a>
# 
# 実装したポートフォリオ最適化を用いて、より現実に近い形での運用シミュレーションを行います。
# 
# シミュレーションは、2024 年 1 月 1 日から始めて 50 営業日を 1 ラウンドとし、全部で 10 ラウンドを行います。1 ラウンドごとに、運用開始日から遡って 50 営業日分のデータを用いてポートフォリオを最適化し株を購入、20 営業日後に売却します。売却して得た資金はすべて次のサイクルの購入資金とします。ただし、より実際に近づけるため、売却するごとに売却益の課税分 (20%) が差し引かれるとします。また、購入・売却金額は終値に対し 0 ～ 1% 増の範囲からランダムに決定した費用とします。
# 
# 以下の図はこのような運用の流れの模式図です。
# 
# ![operation_flow](../figures/portfolio_flow.drawio.svg)
# 

# 1 ラウンド分のシミュレーションを行う関数を作成します。ポートフォリオの作成には、運用開始日よりも前のデータを使用する必要があることに注意します。
# 

# In[ ]:


TAX_RATE = 0.2
rng = np.random.default_rng()


def get_portfolio(
    prices: pd.DataFrame,
    start_date: datetime.date,
    num_days_backward: int,
    num_days_operation: int,
) -> dict[str, int]:
    """過去データを用いて最適化したポートフォリオを取得する

    Args:
        prices (pd.DataFrame): 株価の時系列データ
        start_date (datetime.date): 運用開始日
        num_days_backward (int): 最適化に使用する過去データの日数

    Returns:
        dict[str, int]: 銘柄名をキー、投資比率を値とする辞書
    """

    # 運用開始日の前の営業日を取得
    previous_date = start_date - datetime.timedelta(days=1)

    # 運用開始日からさかのぼって `num_days_backward` 日分の株価データを取得
    stock_price_history = prices.loc[: str(previous_date)].iloc[-num_days_backward:]

    # 運用開始前のデータを用いてポートフォリオを作成
    portfolio, _, _ = optimize_portfolio(stock_price_history, num_days_operation)

    return portfolio


def simulate_stock_trading(
    prices: pd.DataFrame,
    funds: float,
    start_date: datetime.date,
    num_days_operation: int,
    portfolio: dict[str, int],
    tax_rate=TAX_RATE,
) -> float:
    """与えられた運用日数とポートフォリオに基づいて株式売買をシミュレーションする

    Args:
        prices (pd.DataFrame): 株価の時系列データ
        funds (float): 運用資金
        start_date (datetime.date): 運用開始日
        num_days_operation (int): 運用日数
        portfolio (dict[str, int]): ポートフォリオ
        tax_rate (_type_, optional): 譲渡益税率

    Returns:
        float: 運用結果の資金
    """

    # 銘柄ごとの投資比率の配列に変換
    weights = np.array(
        [portfolio.get(stock_name, 0) / 100 for stock_name in prices.columns]
    )

    # 各銘柄の 1 株あたり購入額を前営業日の株価から決定
    previous_date = start_date - datetime.timedelta(days=1)
    start_prices = prices.loc[: str(previous_date)].iloc[-1].to_numpy()
    # 1% 程度の購入価格の増分を考慮
    start_prices = start_prices * rng.uniform(1.0, 1.01, size=len(prices.columns))

    # 各銘柄の 1 株あたり売却額を計算
    end_prices = prices.loc[str(start_date) :].iloc[num_days_operation - 1].to_numpy()
    # 1% 程度の売却金額の差分を考慮
    end_prices = end_prices * rng.uniform(0.99, 1.0, size=len(prices.columns))

    # 利益率を計算
    return_rate: float = (weights * (end_prices / start_prices)).sum()

    # 利益が出た場合は課税分を差し引く
    if return_rate > 1:
        return_rate = 1 + (1 - tax_rate) * (return_rate - 1)

    # 売却額 (= 購入額 x 利益率) を返却
    return funds * return_rate


# 上記の `simulate_stock_trading()` 関数を用いて、複数のラウンドを繰り返しシミュレーションする関数を作成します。この関数は、各ラウンドでの (購入日, 購入額, 売却日, 売却額) を履歴として記録し返却します。
# 

# In[ ]:


def simulate_stick_operation(
    prices: pd.DataFrame,
    num_rounds: int,
    simulation_start_date: datetime.date,
    num_days_sampling: int,
    num_days_operation: int,
) -> list[tuple[datetime.date, float, datetime.date, float]]:
    """与えられた運用日数とサイクル数に基づいて株式売買をシミュレーションする

    Args:
        prices (pd.DataFrame): 株価の時系列データ
        num_rounds (int): ラウンド数
        simulation_start_date (datetime.date): シミュレーションの開始日
        num_days_sampling (int): 最適化に用いる過去データの日数
        num_days_operation (int): 運用日数

    Returns:
        list[tuple[datetime.date, float, datetime.date, float]]: _description_
    """

    # 開始資金
    current_funds = 1.0

    # (購入日, 購入額, 売却日, 売却額) を格納するためのリスト
    operation_history: list[tuple[datetime.date, float, datetime.date, float]] = []

    # シミュレーション開始日以降の株価の時系列データ
    prices_start = prices.loc[str(simulation_start_date) :]

    for i in range(num_rounds):
        # ラウンドの開始日と終了日
        start_date = prices_start.iloc[num_days_operation * i].name.date()  # type: ignore
        end_date = prices_start.iloc[
            num_days_operation * i + num_days_operation - 1
        ].name.date()  # type: ignore

        print(f"Round: {i+1}/{num_rounds}, {start_date} - {end_date}")

        # ポートフォリオの最適化
        portfolio = get_portfolio(
            prices, start_date, num_days_sampling, num_days_operation
        )

        # 株式売買のシミュレーション
        next_funds = simulate_stock_trading(
            prices, current_funds, start_date, num_days_operation, portfolio
        )

        # 運用履歴に追加
        operation_history.append((start_date, current_funds, end_date, next_funds))

        print(
            f"Profit: {next_funds / current_funds:.3f}, Funds: {current_funds:.3f} -> {next_funds:.3f}"
        )

        current_funds = next_funds

    return operation_history


# 以下では、2024/01/01 をシミュレーション開始日として、20 日の運用を 10 回繰り返します。  
# ポートフォリオはそれぞれの運用開始日から遡って 100 日分の過去データを用いて最適化します。  
# セルの実行には 2 分ほどかかるのでご注意ください。
# 

# In[ ]:


operation_history = simulate_stick_operation(
    stock_prices, 10, datetime.date(2024, 1, 1), 100, 20
)
# 最終ラウンドの運用結果
operation_history[-1][3]


# 得られた運用履歴をプロットします。
# 

# In[ ]:


import itertools
import matplotlib.pyplot as plt
from matplotlib import dates as mdates

ax = plt.figure().add_subplot()


def plot(operation_history, color, label):
    for start_date, start_funds, end_date, end_funds in operation_history:
        (line,) = ax.plot(
            [start_date, end_date], [start_funds, end_funds], color=color, marker="o"
        )
    line.set_label(label)  # type: ignore

    for history1, history2 in itertools.pairwise(operation_history):
        _, _, end_date1, end_funds1 = history1
        start_date2, start_funds2, _, _ = history2
        ax.plot(
            [end_date1, start_date2],
            [end_funds1, start_funds2],
            color=color,
            linestyle=":",
        )


plot(operation_history, "C0", "optimized")

ax.legend(loc="lower right")
ax.set_xlabel("Date", fontsize=10)
ax.set_ylabel("Total asset", fontsize=10)
ax.tick_params(labelsize=10)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

plt.show()


# ## 付録
# 
# 以下のようにして、実際の株価のヒストリカルデータを取得することができます。データ取得には `pandas_datareader` を用い、[Stooq](https://stooq.com/) のデータベースからダウンロードしています。銘柄の数と同じ回数だけ API の呼び出しが行われるので、常識の範囲内でご使用ください。
# 
# ```python
# from pandas_datareader import data as web
# 
# 
# def load_historical_data(tickers: list[str], start_date: datetime.date, end_date) -> pd.DataFrame:
#     """Stooq から start_date 以降のヒストリカルデータをダウンロード"""
#     history_df = pd.DataFrame()
#     for idx, ticker in enumerate(tickers):
#         ticker_df: pd.DataFrame = web.DataReader(ticker, "stooq", start_date, end_date)
#         if len(ticker_df) == 0:
#             print(f"failed to get {ticker} data")
#             continue
#         history_df = history_df.join(ticker_df["Close"].rename(ticker), how="outer")
#         print("#", end="\n" if (idx + 1) % 20 == 0 else "")
#     history_df.dropna(how="any", inplace=True) # すべての銘柄が取引された日のみを残す
#     history_df.sort_index(inplace=True)
#     return history_df
# 
# # NASDAQ 100 を構成する銘柄を取得
# tickers = ["ADBE", "ADP", "ABNB", "GOOGL", "GOOG", "AMZN", "AMD", "AEP", "AMGN", "ADI",
#                      "ANSS", "AAPL", "AMAT", "ASML", "AZN", "TEAM", "ADSK", "BKR", "BIIB", "BKNG",
#                      "AVGO", "CDNS", "CDW", "CHTR", "CTAS", "CSCO", "CCEP", "CTSH", "CMCSA", "CEG",
#                      "CPRT", "CSGP", "COST", "CRWD", "CSX", "DDOG", "DXCM", "FANG", "DLTR", "DASH",
#                      "EA", "EXC", "FAST", "FTNT", "GEHC", "GILD", "GFS", "HON", "IDXX", "ILMN",
#                      "INTC", "INTU", "ISRG", "KDP", "KLAC", "KHC", "LRCX", "LIN", "LULU", "MAR",
#                      "MRVL", "MELI", "META", "MCHP", "MU", "MSFT", "MRNA", "MDLZ", "MDB", "MNST",
#                      "NFLX", "NVDA", "NXPI", "ORLY", "ODFL", "ON", "PCAR", "PANW", "PAYX", "PYPL",
#                      "PDD", "PEP", "QCOM", "REGN", "ROP", "ROST", "SIRI", "SBUX", "SNPS", "TTWO",
#                      "TMUS", "TSLA", "TXN", "TTD", "VRSK", "VRTX", "WBA", "WBD", "WDAY", "XEL", "ZS"]
# 
# df = load_historical_data(tickers, datetime.date(2023, 1, 1), datetime.date.today())
# ```
# 
