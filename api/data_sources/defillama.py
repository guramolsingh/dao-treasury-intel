"""
DefiLlama API client.

DefiLlama is the primary data source for this platform because:
- Free, no API key required, no rate limits
- Tracks DAO treasuries across 100+ protocols natively
- Open-source, community-maintained, widely trusted in DeFi
- Returns structured asset breakdowns we can analyze

Endpoints used:
- /protocol/{slug}                  : TVL history + treasury (if available)
- /treasury/{slug}                  : treasury composition by asset
- /protocols                        : full protocol list (for discovery)
- /chains                           : chain TVL data
- /unlocks                          : upcoming token unlocks
- /coins/prices/current/{coin_ids}  : current asset prices
"""
import asyncio
import aiohttp
from typing import Optional

DEFILLAMA_BASE = "https://api.llama.fi"
DEFILLAMA_COINS_BASE = "https://coins.llama.fi"


class DefiLlamaError(Exception):
    """Raised when DefiLlama returns an error or unexpected response."""


class DefiLlamaPaidTierError(DefiLlamaError):
    """Raised when DefiLlama returns 402 — endpoint moved to paid Pro tier."""


async def _get(session: aiohttp.ClientSession, url: str) -> dict:
    """Internal HTTP GET wrapper with consistent error handling."""
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        if resp.status == 402:
            text = await resp.text()
            raise DefiLlamaPaidTierError(f"GET {url} returned 402 (paid tier): {text[:200]}")
        if resp.status != 200:
            text = await resp.text()
            raise DefiLlamaError(f"GET {url} returned {resp.status}: {text[:200]}")
        return await resp.json()


# ============================================================
# TREASURY ENDPOINTS
# ============================================================

async def fetch_treasury(slug: str) -> dict:
    """
    Fetch current treasury composition for a protocol.

    Returns:
        {
          "name": "...",
          "tokens": [
            {"symbol": "USDC", "amount": 12345678, "usd_value": 12345678},
            {"symbol": "OP",   "amount": 250000000, "usd_value": 625000000},
            ...
          ],
          "total_usd": 1234567890,
          "chain_breakdown": {"ethereum": 700000000, "optimism": 534567890},
        }
    """
    url = f"{DEFILLAMA_BASE}/treasury/{slug}"
    async with aiohttp.ClientSession() as session:
        raw = await _get(session, url)

    tokens = []
    chain_breakdown: dict[str, float] = {}
    total_usd = 0.0

    # DefiLlama returns nested structure: chainTvls.{chain}.tokens
    chain_tvls = raw.get("chainTvls", {})
    for chain, chain_data in chain_tvls.items():
        # Skip aggregate keys like "ethereum-borrowed" — we want raw holdings only
        if "-" in chain:
            continue
        chain_total = 0.0
        latest_tokens = chain_data.get("tokensInUsd", [])
        if not latest_tokens:
            continue
        # Last entry is most recent snapshot
        most_recent = latest_tokens[-1].get("tokens", {})
        for symbol, usd in most_recent.items():
            if usd is None or usd < 1:  # skip dust
                continue
            tokens.append({
                "symbol": symbol,
                "chain": chain,
                "usd_value": round(usd, 2),
            })
            chain_total += usd
            total_usd += usd
        chain_breakdown[chain] = round(chain_total, 2)

    # Aggregate by symbol across chains (a DAO may hold USDC on 3 chains)
    by_symbol: dict[str, float] = {}
    for t in tokens:
        by_symbol[t["symbol"]] = by_symbol.get(t["symbol"], 0) + t["usd_value"]

    aggregated = [
        {"symbol": sym, "usd_value": round(val, 2), "pct_of_treasury": round(val / total_usd * 100, 2) if total_usd else 0}
        for sym, val in sorted(by_symbol.items(), key=lambda x: -x[1])
    ]

    return {
        "name": raw.get("name", slug),
        "total_usd": round(total_usd, 2),
        "tokens": aggregated,
        "chain_breakdown": chain_breakdown,
        "as_of": raw.get("lastUpdate"),
    }


# ============================================================
# TOKEN UNLOCKS
# ============================================================

async def fetch_upcoming_unlocks(slug: str, months_ahead: int = 12) -> list[dict]:
    """
    Fetch upcoming token unlocks for the next N months.

    Returns chronological list of {date, amount_tokens, usd_value, category}.
    """
    # v1 limitation: DefiLlama moved /emissions/{slug} behind their paid Pro tier
    # in 2026 (returns HTTP 402 on the free endpoint for every DAO we track).
    # We swallow that error and return [] so the rest of the analysis pipeline
    # still runs. Unlock tracking will move to TokenUnlocks.app or DefiLlama Pro
    # in v2 — see docs/methodology.md "Limitations".
    url = f"{DEFILLAMA_BASE}/emissions/{slug}"
    try:
        async with aiohttp.ClientSession() as session:
            raw = await _get(session, url)
    except DefiLlamaPaidTierError:
        return []

    events = raw.get("events", [])
    # Each event: {timestamp, noOfTokens (list per category), description}
    upcoming = []
    import time
    now_ts = time.time()
    horizon_ts = now_ts + months_ahead * 30 * 86400

    for event in events:
        ts = event.get("timestamp", 0)
        if ts < now_ts or ts > horizon_ts:
            continue
        upcoming.append({
            "timestamp": ts,
            "tokens_unlocked": sum(event.get("noOfTokens", []) or [0]),
            "description": event.get("description", ""),
        })

    return sorted(upcoming, key=lambda x: x["timestamp"])


# ============================================================
# TVL & PROTOCOL DATA
# ============================================================

async def fetch_protocol_tvl(slug: str) -> dict:
    """Fetch current TVL and 30-day history for a protocol."""
    url = f"{DEFILLAMA_BASE}/protocol/{slug}"
    async with aiohttp.ClientSession() as session:
        raw = await _get(session, url)

    tvl_history = raw.get("tvl", [])
    if not tvl_history:
        return {"current_tvl": 0, "history_30d": []}

    history = [
        {"timestamp": entry["date"], "tvl_usd": round(entry["totalLiquidityUSD"], 2)}
        for entry in tvl_history[-30:]
    ]
    return {
        "current_tvl": history[-1]["tvl_usd"] if history else 0,
        "tvl_30d_ago": history[0]["tvl_usd"] if history else 0,
        "tvl_change_pct_30d": round(
            (history[-1]["tvl_usd"] / history[0]["tvl_usd"] - 1) * 100, 2
        ) if history and history[0]["tvl_usd"] > 0 else 0,
        "history_30d": history,
    }


# ============================================================
# BATCH FETCH
# ============================================================

async def fetch_all_for_dao(slug: str) -> dict:
    """
    Fetch treasury + TVL + unlocks for a single DAO in parallel.

    This is the main entry point — one call per DAO returns
    everything we need for the analysis layer.
    """
    treasury, tvl, unlocks = await asyncio.gather(
        fetch_treasury(slug),
        fetch_protocol_tvl(slug),
        fetch_upcoming_unlocks(slug),
        return_exceptions=True,
    )

    # Treat exceptions as empty data (one bad endpoint shouldn't kill the call)
    return {
        "treasury": treasury if not isinstance(treasury, Exception) else None,
        "tvl": tvl if not isinstance(tvl, Exception) else None,
        "unlocks": unlocks if not isinstance(unlocks, Exception) else [],
    }
