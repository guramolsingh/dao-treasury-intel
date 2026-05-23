"""
Treasury analysis layer.

Takes raw data from DefiLlama and produces the actual insights:
- Asset concentration risk (Herfindahl-style)
- Native token exposure (what % is denominated in the DAO's own token)
- Runway calculation under price scenarios
- Comparative metrics for cross-DAO views

All calculations are deterministic. No AI in this layer — Claude
only narrates these numbers, never computes them.
"""
from typing import Optional


# ============================================================
# CONCENTRATION RISK
# ============================================================

def calculate_concentration_risk(treasury: dict) -> dict:
    """
    How concentrated is the treasury?

    Returns:
        herfindahl_index   : 0-10000, higher = more concentrated
        top_asset_pct      : % of treasury in single largest asset
        top_3_pct          : % of treasury in top 3 assets
        diversification    : "Concentrated" | "Moderate" | "Diversified"
    """
    tokens = treasury.get("tokens", [])
    if not tokens:
        return {"herfindahl_index": 0, "top_asset_pct": 0, "top_3_pct": 0, "diversification": "Unknown"}

    pcts = [t["pct_of_treasury"] for t in tokens]
    herfindahl = sum(p * p for p in pcts)  # 0-10000 (100% squared = 10000)

    top_pct = pcts[0] if pcts else 0
    top_3_pct = sum(pcts[:3])

    if herfindahl > 5000:
        diversification = "Concentrated"
    elif herfindahl > 2500:
        diversification = "Moderate"
    else:
        diversification = "Diversified"

    return {
        "herfindahl_index": round(herfindahl, 0),
        "top_asset_pct": round(top_pct, 2),
        "top_3_pct": round(top_3_pct, 2),
        "diversification": diversification,
    }


# ============================================================
# NATIVE TOKEN EXPOSURE
# ============================================================

def calculate_native_exposure(treasury: dict, native_ticker: str) -> dict:
    """
    What fraction of the treasury is denominated in the DAO's own token?

    This is the single most important risk metric for DAO treasuries.
    A DAO holding 80% of treasury in its own token sees runway evaporate
    in a bear market — the asset and the obligation correlate perfectly.
    """
    tokens = treasury.get("tokens", [])
    native = next((t for t in tokens if t["symbol"].upper() == native_ticker.upper()), None)

    if not native:
        return {
            "native_pct": 0,
            "native_usd": 0,
            "stable_pct": 0,
            "other_pct": 100,
            "risk_signal": "Low — no native token exposure detected",
        }

    native_pct = native["pct_of_treasury"]
    stables = {"USDC", "USDT", "DAI", "USDS", "FRAX", "LUSD", "GHO"}
    stable_pct = sum(t["pct_of_treasury"] for t in tokens if t["symbol"].upper() in stables)
    other_pct = max(0, 100 - native_pct - stable_pct)

    if native_pct > 70:
        risk = "Critical — extreme native token concentration, runway correlates with token price"
    elif native_pct > 50:
        risk = "High — majority native exposure, bear-case runway materially compromised"
    elif native_pct > 30:
        risk = "Moderate — meaningful native exposure, treasury partially price-sensitive"
    else:
        risk = "Low — diversified holdings reduce price correlation"

    return {
        "native_pct": round(native_pct, 2),
        "native_usd": round(native["usd_value"], 2),
        "stable_pct": round(stable_pct, 2),
        "other_pct": round(other_pct, 2),
        "risk_signal": risk,
    }


# ============================================================
# RUNWAY CALCULATIONS
# ============================================================

def estimate_burn_rate(treasury_history: list[dict]) -> Optional[float]:
    """
    Estimate monthly burn rate from treasury value history.

    Naive approach: average monthly USD decline over the observation window.
    Returns None if history is too short or treasury is growing.
    """
    if len(treasury_history) < 2:
        return None

    first = treasury_history[0]["total_usd"]
    last = treasury_history[-1]["total_usd"]
    months = max(1, len(treasury_history) / 30)  # daily snapshots

    if last >= first:
        return None  # growing, not burning

    return (first - last) / months


def calculate_runway(
    treasury_total_usd: float,
    monthly_burn_usd: float,
    native_pct: float,
    price_scenarios: dict[str, float],
) -> dict:
    """
    Runway in months under three token price scenarios.

    Treasury value adjusts based on what % is in native token —
    a 50% drop in token price reduces a 60%-native treasury by 30%.

    Args:
        price_scenarios: {"bear": 0.3, "base": 1.0, "bull": 3.0} as multipliers
    """
    if monthly_burn_usd <= 0:
        return {scenario: {"runway_months": None, "adjusted_treasury": treasury_total_usd}
                for scenario in price_scenarios}

    out = {}
    for scenario, multiplier in price_scenarios.items():
        # Native portion adjusts with price; non-native stays flat
        native_value = treasury_total_usd * (native_pct / 100) * multiplier
        non_native_value = treasury_total_usd * (1 - native_pct / 100)
        adjusted = native_value + non_native_value
        out[scenario] = {
            "runway_months": round(adjusted / monthly_burn_usd, 1),
            "adjusted_treasury": round(adjusted, 2),
            "price_multiplier": multiplier,
        }
    return out


# ============================================================
# COMPARATIVE METRICS
# ============================================================

def comparative_summary(dao_outputs: dict[str, dict]) -> list[dict]:
    """
    Build a side-by-side comparison row per DAO.
    Used by the comparison view in the frontend.
    """
    rows = []
    for slug, data in dao_outputs.items():
        treasury = data.get("treasury") or {}
        concentration = data.get("concentration") or {}
        exposure = data.get("native_exposure") or {}
        tvl = data.get("tvl") or {}

        rows.append({
            "slug": slug,
            "treasury_total_usd": treasury.get("total_usd", 0),
            "tvl_usd": tvl.get("current_tvl", 0),
            "treasury_to_tvl_ratio": round(
                (treasury.get("total_usd", 0) / tvl.get("current_tvl", 1)) * 100, 2
            ) if tvl.get("current_tvl") else 0,
            "native_pct": exposure.get("native_pct", 0),
            "stable_pct": exposure.get("stable_pct", 0),
            "diversification": concentration.get("diversification", "Unknown"),
            "herfindahl_index": concentration.get("herfindahl_index", 0),
        })

    return sorted(rows, key=lambda r: -r["treasury_total_usd"])


# ============================================================
# FULL ANALYSIS PIPELINE
# ============================================================

def analyze_dao(raw_data: dict, dao_config: dict, monthly_burn_usd: float = 1_000_000) -> dict:
    """
    Run the full analysis pipeline on one DAO's raw data.

    This is the function the API endpoint calls.
    """
    treasury = raw_data.get("treasury")
    if not treasury or treasury.get("total_usd", 0) == 0:
        return {"error": f"No treasury data available for {dao_config['display_name']}"}

    concentration = calculate_concentration_risk(treasury)
    exposure = calculate_native_exposure(treasury, dao_config["ticker"])
    runway = calculate_runway(
        treasury["total_usd"],
        monthly_burn_usd,
        exposure["native_pct"],
        price_scenarios={"bear": 0.3, "base": 1.0, "bull": 3.0},
    )

    return {
        "dao": dao_config["display_name"],
        "ticker": dao_config["ticker"],
        "category": dao_config["category"],
        "treasury": treasury,
        "tvl": raw_data.get("tvl"),
        "upcoming_unlocks": raw_data.get("unlocks", [])[:6],  # next 6 events
        "concentration": concentration,
        "native_exposure": exposure,
        "runway": runway,
        "monthly_burn_assumption": monthly_burn_usd,
    }
