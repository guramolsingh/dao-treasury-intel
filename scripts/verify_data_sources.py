"""
Verify that every DAO in the registry returns usable treasury data.

Hits DefiLlama for each configured DAO in parallel and prints a one-line
status per protocol: treasury USD total, token count, and whether the
unlocks endpoint produced anything (it's behind DefiLlama's paid tier as
of 2026 — see docs/methodology.md "Limitations").

Run from the repo root:

    python scripts/verify_data_sources.py
"""
import asyncio
import sys
from pathlib import Path

# Allow `python scripts/verify_data_sources.py` from the repo root without
# installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import DAO_REGISTRY
from api.data_sources.defillama import fetch_all_for_dao


async def _verify_one(slug: str, cfg: dict) -> dict:
    treasury_slug = cfg["defillama_treasury_slug"]
    try:
        raw = await fetch_all_for_dao(treasury_slug)
    except Exception as e:
        return {"slug": slug, "ok": False, "error": str(e)}

    treasury = raw.get("treasury") or {}
    return {
        "slug": slug,
        "display_name": cfg["display_name"],
        "treasury_slug": treasury_slug,
        "ok": bool(treasury.get("total_usd")),
        "total_usd": treasury.get("total_usd"),
        "token_count": len(treasury.get("tokens") or []),
        "tvl_usd": (raw.get("tvl") or {}).get("current_tvl"),
        "unlocks_count": len(raw.get("unlocks") or []),
    }


async def main() -> int:
    results = await asyncio.gather(
        *[_verify_one(slug, cfg) for slug, cfg in DAO_REGISTRY.items()]
    )

    print(f"{'DAO':<12} {'slug':<22} {'treasury USD':>16} {'tokens':>8} {'unlocks':>8}  status")
    print("-" * 90)
    ok_count = 0
    for r in results:
        if r["ok"]:
            ok_count += 1
            total = f"${r['total_usd']:,.0f}"
            print(
                f"{r['slug']:<12} {r['treasury_slug']:<22} {total:>16} "
                f"{r['token_count']:>8} {r['unlocks_count']:>8}  OK"
            )
        else:
            err = r.get("error", "no treasury data returned")
            print(f"{r['slug']:<12} {'-':<22} {'-':>16} {'-':>8} {'-':>8}  FAIL — {err[:60]}")

    print("-" * 90)
    print(f"{ok_count}/{len(results)} DAOs returned treasury data.")
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
