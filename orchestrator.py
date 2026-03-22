"""
副業戦略チーム オーケストレーター
各エージェントを独立したサブエージェントとして並列実行する
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage


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

【出力形式の注意】
表や箇条書きだけでなく、必ず各項目について「なぜそれが重要か」「どういう意味を持つか」を日本語の文章で説明してください。
データや数値を示す場合も、その数値が何を意味するのかを一言添えてください。
読んだだけで全体像が掴めるよう、導入文と締めの考察も書いてください。

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

【出力形式の注意】
表や箇条書きだけでなく、必ず各項目について「なぜそれが重要か」「どういう意味を持つか」を日本語の文章で説明してください。
ハッシュタグや傾向を列挙するだけでなく、それぞれが何を示しているのか・どう活用できるのかを具体的に解説してください。
読んだだけで全体像が掴めるよう、導入文と締めの考察も書いてください。

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

【出力形式の注意】
表や箇条書きだけでなく、必ず各項目について「なぜそれが重要か」「どういう意味を持つか」を日本語の文章で説明してください。
数値・価格帯・競合情報を示す際は、それが中村賢治の副業にとってどんな意味を持つかを解説してください。
読んだだけで全体像が掴めるよう、導入文と締めの考察も書いてください。

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

【出力形式の注意】
ロードマップや数値は表や箇条書きで示してもよいですが、必ず各フェーズについて「なぜこの順番なのか」「何が重要なポイントか」を文章で説明してください。
数字（投資額・収益・工数）は根拠とともに説明し、読んだ人が「なるほど」と理解できるようにしてください。
導入文で全体像を示し、最後に「まず何をすべきか」を文章でまとめてください。

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

【出力形式の注意】
チャネルやステップを列挙するだけでなく、「なぜそのチャネルなのか」「なぜその順番なのか」を文章で説明してください。
中村賢治というブランドが持つ強みと、それをどう発信に活かすかを具体的な言葉で解説してください。
読み終えたら「自分でもできそう」と思えるくらい、背景と理由が分かる文章にしてください。

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

【出力形式の注意】
問題点を箇条書きで並べるだけでなく、各リスクについて「なぜそれが問題になるか」「どういうシナリオで失敗するか」を具体的な文章で説明してください。
数字や事例を使って根拠を示し、感情論ではなくロジックで説明してください。
最後に「最も致命的なリスク」を1つ選んでその理由を文章でまとめてください。

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

【出力形式の注意】
TODOリストや表は使ってよいですが、必ず各アクションについて「なぜこれをやるのか」「何を目指してやるのか」を文章で説明してください。
改善版プランがなぜ元の提案より優れているのかを、批判を踏まえた上で言葉で説明してください。
最後に「中村賢治へのメッセージ」として、明日からの最初の一歩を励ましの言葉とともに文章でまとめてください。

全エージェントの結果：{all_results}
"""
}


async def run_agent(agent_name: str, prompt: str) -> str:
    """単一エージェントを非同期実行する"""
    print(f"▶ {agent_name} 起動中...")
    result = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            model="claude-opus-4-6",
            allowed_tools=[],
            max_turns=3,
        )
    ):
        if isinstance(message, ResultMessage):
            result = message.result
    print(f"✅ {agent_name} 完了")
    return result


async def orchestrate(theme: str):
    """全エージェントをオーケストレートして最終結果を返す"""

    print(f"\n副業戦略チーム起動 テーマ：{theme}\n")

    # Phase 1：A・B・C 並列調査
    print("Phase 1：A・B・C 並列調査中...")
    research = {}

    async def collect(name, prompt):
        research[name] = await run_agent(name, prompt)

    async with anyio.create_task_group() as tg:
        tg.start_soon(collect, "A_twitter",   AGENTS["A_twitter"].format(theme=theme))
        tg.start_soon(collect, "B_instagram", AGENTS["B_instagram"].format(theme=theme))
        tg.start_soon(collect, "C_market",    AGENTS["C_market"].format(theme=theme))

    research_summary = "\n\n".join([f"【{k}】\n{v}" for k, v in research.items()])

    # Phase 2：D 戦略立案
    print("\nPhase 2：D 戦略立案中...")
    strategy = await run_agent("D_strategy", AGENTS["D_strategy"].format(research_results=research_summary))

    # Phase 3：E マーケティング
    print("\nPhase 3：E マーケティング中...")
    marketing = await run_agent("E_marketing", AGENTS["E_marketing"].format(strategy=strategy))

    # Phase 4：F 批判
    print("\nPhase 4：F 批判中...")
    criticism = await run_agent("F_critic", AGENTS["F_critic"].format(proposals=f"{strategy}\n{marketing}"))

    # Phase 5：G まとめ
    print("\nPhase 5：G まとめ中...")
    all_results = f"調査：{research_summary}\n戦略：{strategy}\nマーケ：{marketing}\n批判：{criticism}"
    final = await run_agent("G_summary", AGENTS["G_summary"].format(all_results=all_results))

    print("\n✅ 全エージェント完了\n")
    print("=" * 60)
    print("【最終提案】")
    print("=" * 60)
    print(final)

    return final


if __name__ == "__main__":
    theme = input("副業テーマを入力してください：")
    anyio.run(orchestrate, theme)
