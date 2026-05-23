"""
AI memo layer — Claude takes computed analysis output and writes
a research-grade treasury health memo.

Critical design decision: Claude NEVER does math. The analysis module
already computed everything. Claude's job is interpretation and synthesis,
not calculation. This is the same architectural pattern as the
SaaS Scenario Engine — eliminates AI arithmetic errors in financial output.
"""
import os
from anthropic import Anthropic

_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def build_memo_prompt(analysis: dict) -> str:
    """
    Construct a structured prompt that gives Claude the numbers
    AND tells it exactly what kind of memo to write.
    """
    treasury = analysis["treasury"]
    concentration = analysis["concentration"]
    exposure = analysis["native_exposure"]
    runway = analysis["runway"]
    tvl = analysis.get("tvl") or {}

    top_holdings = "\n".join(
        f"  - {t['symbol']:8s} ${t['usd_value']:>15,.0f} ({t['pct_of_treasury']}%)"
        for t in treasury["tokens"][:5]
    )

    return f"""You are a senior research analyst at a crypto-native investment firm writing a treasury health memo for institutional readers. The numerical analysis is complete — interpret it, don't recalculate.

PROTOCOL: {analysis['dao']} ({analysis['ticker']}) · {analysis['category']}

TREASURY COMPOSITION (${treasury['total_usd']:,.0f} total):
{top_holdings}

CONCENTRATION METRICS:
  - Diversification: {concentration['diversification']}
  - Herfindahl index: {concentration['herfindahl_index']} (0-10000 scale)
  - Top asset: {concentration['top_asset_pct']}% of treasury
  - Top 3 assets: {concentration['top_3_pct']}% of treasury

NATIVE TOKEN EXPOSURE:
  - Native ({analysis['ticker']}): {exposure['native_pct']}% of treasury
  - Stablecoins: {exposure['stable_pct']}%
  - Other: {exposure['other_pct']}%
  - Risk signal: {exposure['risk_signal']}

RUNWAY UNDER PRICE SCENARIOS (assuming ${analysis['monthly_burn_assumption']:,}/mo burn):
  - Bear (token at 30% of current): {runway['bear']['runway_months']} months
  - Base (current token price):      {runway['base']['runway_months']} months
  - Bull (token at 300% of current): {runway['bull']['runway_months']} months

TVL CONTEXT:
  - Current TVL: ${tvl.get('current_tvl', 0):,.0f}
  - 30-day change: {tvl.get('tvl_change_pct_30d', 0)}%

Write a 3-paragraph memo with this structure:

PARAGRAPH 1 — TREASURY HEALTH ASSESSMENT
Lead with the single most important finding. Is this treasury well-positioned or vulnerable? Reference specific numbers (the native exposure %, the bear-case runway). Two to three sentences.

PARAGRAPH 2 — KEY RISKS
Focus on the gap between scenarios. What happens to operational capacity in the bear case? Are there structural issues (over-concentration, native correlation)? Reference the Herfindahl reading or top-asset concentration. Two to three sentences.

PARAGRAPH 3 — RECOMMENDATIONS
Specific, actionable. Examples: rebalance toward stablecoins by X%, set treasury policy floor of Y% in non-correlated assets, hedge native exposure via options. Three sentences max.

Tone: senior crypto analyst writing for institutional readers (think Delphi Digital, Messari Pro). Quantitative. No hype. No bullet points within the memo. No filler phrases like "it is worth noting." Get to the substance.
"""


def generate_memo(analysis: dict) -> dict:
    """
    Call Claude to generate the treasury health memo.
    Returns the memo text and metadata.
    """
    prompt = build_memo_prompt(analysis)

    response = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "memo": response.content[0].text,
        "model": "claude-sonnet-4-5",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def generate_comparison_memo(comparative_rows: list[dict]) -> dict:
    """
    Generate a cross-DAO comparison memo.
    Used by the comparison view that ranks DAOs by treasury health.
    """
    table = "\n".join(
        f"  {r['slug']:10s} | ${r['treasury_total_usd']:>15,.0f} | Native: {r['native_pct']:>5}% | Stable: {r['stable_pct']:>5}% | {r['diversification']}"
        for r in comparative_rows
    )

    prompt = f"""You are writing a comparative DAO treasury memo for institutional crypto investors.

COMPARATIVE DATA:
{table}

Write 3 paragraphs:
1. Which DAO has the strongest treasury position and why (cite the numbers).
2. Which DAO has the most concerning concentration risk and why.
3. A general observation about DAO treasury management based on this dataset.

Keep it tight. No bullet points. Reference specific protocols and specific numbers."""

    response = _client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"memo": response.content[0].text, "model": "claude-sonnet-4-5"}
