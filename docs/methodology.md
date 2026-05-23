# Methodology

The technical and analytical decisions behind this platform.

## Why DefiLlama as the primary source

DefiLlama is the canonical free source for DAO treasury data because:

1. **Community-trusted**: Maintained by an open-source team since 2020. Used by Coinbase research, Galaxy Digital reports, and most DeFi analysts.
2. **Multi-sig aware**: They handle the complex mapping between a DAO's name and its multi-sig addresses across chains. We don't have to maintain that registry ourselves.
3. **Free with no key**: Unlike Etherscan, CoinGecko, or Alchemy, DefiLlama imposes no rate limits on basic endpoints. This makes the project sustainable to run for free.
4. **Multi-chain**: A single DAO often holds assets across Ethereum, Optimism, Arbitrum, and Base. DefiLlama aggregates these natively.

The trade-off: DefiLlama is updated hourly, not in real-time. For institutional treasury monitoring this is acceptable. For HFT or MEV use cases it wouldn't be.

## Concentration metrics

We use a Herfindahl-Hirschman-style index calculated on treasury composition.

For a treasury with assets at percentages p₁, p₂, ..., pₙ:

```
H = Σ (pᵢ)²
```

This produces a value from 0 to 10,000 where:
- **H < 2,500**: Diversified (no single asset dominates)
- **2,500 ≤ H < 5,000**: Moderate concentration
- **H ≥ 5,000**: Concentrated (typically driven by one outsized native token position)

Why Herfindahl rather than just "% in top asset": it captures both the dominance of the largest holding AND the long-tail distribution. A treasury at 60/40 split has higher Herfindahl than a 60/20/20 split, even though the top asset is identical.

## Native token exposure risk thresholds

The single most important treasury risk for a DAO is correlation between asset value and obligation. When a DAO holds 80% of its treasury in its own token, a 50% drawdown reduces both the treasury and the perceived solvency of the protocol simultaneously.

Risk tiers we apply:
- **> 70% native**: Critical. Runway evaporates in any meaningful drawdown.
- **50-70% native**: High. Bear-case runway materially compromised.
- **30-50% native**: Moderate. Treasury partially price-sensitive.
- **< 30% native**: Low. Diversified holdings buffer against price moves.

These thresholds are calibrated against historical DAO performance through the 2022 crypto bear market, when several protocols with > 70% native exposure saw effective runway drop by 60-80%.

## Runway calculation

Standard finance approach with one adjustment for crypto:

```
adjusted_treasury = (native_pct × treasury_total × price_multiplier)
                  + (non_native_pct × treasury_total)

runway_months = adjusted_treasury / monthly_burn_usd
```

The key insight is that not all treasury value should be marked-to-market against price scenarios. A treasury holding 30% USDC and 70% native token will see 70% of its value flex with the token price, but 30% stays nominally flat (assuming the stablecoin holds peg, which is its own risk).

Price scenarios applied:
- **Bear**: 0.3× current price (−70%)
- **Base**: 1.0× current price
- **Bull**: 3.0× current price (+200%)

These multipliers are not predictions. They are stress-test inputs calibrated against historical DAO token volatility. Adjust as appropriate for specific protocols.

## Why Claude only narrates, never calculates

This is a deliberate architectural decision.

Large language models are excellent at translating structured analytical outputs into prose that sounds like a senior analyst wrote it. They are unreliable at arithmetic, especially when the calculation involves multiple steps or large numbers.

By computing all financial metrics in Python first and passing those metrics as structured inputs to the AI prompt, we get:

1. **Auditable outputs**: Every number in the memo can be traced to a deterministic calculation.
2. **Eliminates AI arithmetic errors**: A common failure mode where the AI confidently states "$847M runway" when the actual figure is $84.7M.
3. **Better memos**: The AI can focus on interpretation and synthesis rather than re-deriving values.

This same pattern is used in production FP&A tools at financial institutions.

## Limitations

Known limitations of the current v1:

1. **Burn rate is assumed, not measured.** We default to $1M/month per DAO. A more sophisticated version would estimate burn from treasury outflows over the prior 90 days. This is on the v2 roadmap.

2. **Off-balance-sheet obligations are not captured.** A DAO with active grants programs, vested contributor agreements, or insurance obligations has effective burn higher than what shows in treasury outflows. This requires manual input per DAO.

3. **Native price scenarios are static.** A truly rigorous model would use historical volatility per token to size scenarios proportionally. Current implementation uses flat ±70% / +200% multipliers.

4. **No governance integration yet.** Snapshot and Tally APIs are integrated in the v2 roadmap, allowing the memo to factor in pending proposals that affect treasury (e.g., a grants program expansion changes the burn rate assumption).

These are deliberate v1 limitations to ship something useful quickly. The point of the platform is to be 80% as good as institutional DAO treasury analysis at 0% of the cost — not to replace dedicated treasury teams at major protocols.
