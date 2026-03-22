"""
副業戦略チーム オーケストレーター
各エージェントを独立したサブエージェントとして並列実行する
"""

import anthropic
import concurrent.futures

client = anthropic.Anthropic()

# ========== 各エージェントの指示 ==========

AGENTS = {
    "A_twitter": """
あなたはTwitter調査専門エージェントです。
以下のテーマについてTwitterの観点から調査してください。

調査内容：
- 関連するトレンドワード
- 同じ分野で発信している人の反応・フォロワー数
- 需要がありそうなテーマ・悩み
- 具体例・数値を含めて報告

テーマ：{theme}
""",

    "B_instagram": """
あなたはInstagram調査専門エージェントです。
以下のテーマについてInstagramの観点から調査してください。

調査内容：
- 関連する人気ハッシュタグ
- エンゲージメント率の高い投稿の傾向
- ビジュアル・世界観・発信スタイルのトレンド
- 競合アカウントの戦略

テーマ：{theme}
""",

    "C_market": """
あなたは市場調査専門エージェントです。
以下のテーマについて市場の観点から調査してください。

調査内容：
- 市場規模・成長性・収益性
- 競合他社・個人の価格帯・サービス内容
- 参入障壁・差別化ポイント
- 中村賢治のスキル（環境管理・Python・仮想通貨）で勝てる市場かどうか

テーマ：{theme}
""",

    "D_strategy": """
あなたは副業戦略専門エージェントです。
以下の調査結果を踏まえて副業戦略を立案してください。

ユーザー情報：
- 名前：中村賢治
- スキル：環境管理・法令対応・Python・自動化・仮想通貨シグナル開発

提案内容：
- 具体的な副業プラン
- 短期（3ヶ月）・中期（1年）・長期（3年）の収益化ロードマップ
- 初期投資・月間工数・想定収益
- 最初のアクション

調査結果：{research_results}
""",

    "E_marketing": """
あなたはマーケティング専門エージェントです。
以下の戦略に対してマーケティング戦略を立案してください。

提案内容：
- 発信チャネル・ターゲット・メッセージ
- コンテンツ戦略・投稿頻度・世界観
- 中村賢治のブランドとしての差別化ポイント
- 最初の100人獲得までの具体的なステップ

戦略：{strategy}
""",

    "F_critic": """
あなたは批判的分析専門エージェントです。
以下の提案に対して徹底的に問題点を指摘してください。

指摘内容：
- なぜうまくいかないか（具体的根拠付き）
- 市場リスク・時間コスト・収益化の難しさ
- 見落としている視点・競合優位性の弱点
- 感情論ではなく根拠を持って反論する

提案内容：{proposals}
""",

    "G_summary": """
あなたはまとめ専門エージェントです。
批判的意見を全て踏まえた上で最終的な改善プランをまとめてください。

まとめ内容：
- 批判を全て反映した改善版プラン
- リスクを最小化しながら収益を最大化する方法
- 中村賢治が明日から動けるレベルの具体的アクションプラン
- 優先順位付きのTODOリスト

全エージェントの結果：{all_results}
"""
}


def run_agent(agent_name: str, prompt: str) -> str:
    """単一エージェントを実行する"""
    print(f"▶ {agent_name} 起動中...")
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    result = response.content[0].text
    print(f"✅ {agent_name} 完了")
    return result


def orchestrate(theme: str):
    """全エージェントをオーケストレートして最終結果を返す"""

    print(f"\n副業戦略チーム起動 テーマ：{theme}\n")

    # Phase 1：A・B・C 並列調査
    print("Phase 1：A・B・C 並列調査中...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(run_agent, "A_twitter", AGENTS["A_twitter"].format(theme=theme)): "A_twitter",
            executor.submit(run_agent, "B_instagram", AGENTS["B_instagram"].format(theme=theme)): "B_instagram",
            executor.submit(run_agent, "C_market", AGENTS["C_market"].format(theme=theme)): "C_market",
        }
        research = {}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            research[name] = future.result()

    research_summary = "\n\n".join([f"【{k}】\n{v}" for k, v in research.items()])

    # Phase 2：D 戦略立案
    print("\nPhase 2：D 戦略立案中...")
    strategy = run_agent("D_strategy", AGENTS["D_strategy"].format(research_results=research_summary))

    # Phase 3：E マーケティング
    print("\nPhase 3：E マーケティング中...")
    marketing = run_agent("E_marketing", AGENTS["E_marketing"].format(strategy=strategy))

    # Phase 4：F 批判
    print("\nPhase 4：F 批判中...")
    criticism = run_agent("F_critic", AGENTS["F_critic"].format(proposals=f"{strategy}\n{marketing}"))

    # Phase 5：G まとめ
    print("\nPhase 5：G まとめ中...")
    all_results = f"調査：{research_summary}\n戦略：{strategy}\nマーケ：{marketing}\n批判：{criticism}"
    final = run_agent("G_summary", AGENTS["G_summary"].format(all_results=all_results))

    print("\n✅ 全エージェント完了\n")
    print("="*60)
    print("【最終提案】")
    print("="*60)
    print(final)

    return final


if __name__ == "__main__":
    theme = input("副業テーマを入力してください：")
    orchestrate(theme)
