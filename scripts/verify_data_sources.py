"""
Verify that DefiLlama returns usable data for each registered DAO.

Runs `fetch_all_for_dao` against every entry in `DAO_REGISTRY` and
reports, per DAO, whether the treasury, TVL, and unlocks endpoints
produced valid data — plus the treasury total USD value when present.
Because `fetch_all_for_dao` swallows per-endpoint exceptions (returning
`None` / `[]`), this script re-calls the underlying fetcher directly
when an endpoint comes back empty so the actual error can be surfaced.
"""
import asyncio
import sys
from pathlib import Path

# Allow running as `python scripts/verify_data_sources.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import DAO_REGISTRY
from api.data_sources.defillama import (
    fetch_all_for_dao,
    fetch_treasury,
    fetch_protocol_tvl,
    fetch_upcoming_unlocks,
)


async def _diagnose(slug: str, endpoint: str) -> str:
    """Re-call a single endpoint directly to capture the error message."""
    try:
        if endpoint == "treasury":
            await fetch_treasury(slug)
        elif endpoint == "tvl":
            await fetch_protocol_tvl(slug)
        elif endpoint == "unlocks":
            await fetch_upcoming_unlocks(slug)
        return "empty response (no exception on retry)"
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def _fmt_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"


async def verify_dao(slug: str) -> dict:
    meta = DAO_REGISTRY[slug]
    result: dict = {"slug": slug, "name": meta["display_name"], "endpoints": {}}

    try:
        data = await fetch_all_for_dao(slug)
    except Exception as exc:
        result["fatal"] = f"{type(exc).__name__}: {exc}"
        return result

    treasury = data.get("treasury")
    tvl = data.get("tvl")
    unlocks = data.get("unlocks")

    if treasury and treasury.get("total_usd", 0) > 0:
        result["endpoints"]["treasury"] = {
            "ok": True,
            "total_usd": treasury["total_usd"],
            "token_count": len(treasury.get("tokens", [])),
        }
    else:
        result["endpoints"]["treasury"] = {
            "ok": False,
            "error": await _diagnose(slug, "treasury"),
        }

    if tvl and tvl.get("current_tvl", 0) > 0:
        result["endpoints"]["tvl"] = {"ok": True, "current_tvl": tvl["current_tvl"]}
    else:
        result["endpoints"]["tvl"] = {
            "ok": False,
            "error": await _diagnose(slug, "tvl"),
        }

    if unlocks:
        result["endpoints"]["unlocks"] = {"ok": True, "count": len(unlocks)}
    else:
        result["endpoints"]["unlocks"] = {
            "ok": False,
            "error": await _diagnose(slug, "unlocks"),
        }

    return result


def _print_report(rows: list[dict]) -> None:
    print()
    print("=" * 78)
    print(f"{'DAO':<22} {'Treasury':<22} {'TVL':<18} {'Unlocks':<12}")
    print("=" * 78)
    for r in rows:
        if "fatal" in r:
            print(f"{r['name']:<22} FATAL: {r['fatal']}")
            continue
        eps = r["endpoints"]
        t = eps["treasury"]
        treasury_col = f"OK  {_fmt_usd(t['total_usd'])}" if t["ok"] else "FAIL"
        tvl_col = f"OK  {_fmt_usd(eps['tvl']['current_tvl'])}" if eps["tvl"]["ok"] else "FAIL"
        unlocks_col = f"OK  ({eps['unlocks']['count']})" if eps["unlocks"]["ok"] else "FAIL"
        print(f"{r['name']:<22} {treasury_col:<22} {tvl_col:<18} {unlocks_col:<12}")
    print("=" * 78)

    print("\nDetails for failing endpoints:")
    any_fail = False
    for r in rows:
        if "fatal" in r:
            any_fail = True
            print(f"  - {r['slug']}: FATAL {r['fatal']}")
            continue
        for ep_name, ep in r["endpoints"].items():
            if not ep["ok"]:
                any_fail = True
                print(f"  - {r['slug']}.{ep_name}: {ep['error']}")
    if not any_fail:
        print("  (none — all endpoints returned data)")
    print()


async def main() -> int:
    rows = await asyncio.gather(*(verify_dao(slug) for slug in DAO_REGISTRY))
    _print_report(list(rows))
    failures = sum(
        1 for r in rows
        if "fatal" in r or any(not ep["ok"] for ep in r["endpoints"].values())
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
