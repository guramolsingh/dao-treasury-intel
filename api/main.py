"""
FastAPI entry point — DAO Treasury Intelligence Platform.

Routes:
  GET  /api/daos                : List all tracked DAOs
  GET  /api/dao/{slug}          : Full treasury analysis for one DAO
  GET  /api/compare             : Side-by-side comparison of all tracked DAOs
  POST /api/memo/{slug}         : Generate AI memo for a specific DAO
  POST /api/memo/comparison     : Generate cross-DAO comparison memo
  GET  /api/health              : Liveness check
"""
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.config import DAO_REGISTRY, get_dao, list_daos
from api.data_sources.defillama import fetch_all_for_dao
from api.analysis.treasury import analyze_dao, comparative_summary
from api.ai.memo import generate_memo, generate_comparison_memo

app = FastAPI(title="DAO Treasury Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory cache. DefiLlama is free but courteous to cache.
# In production: use Vercel KV (also free tier) or Redis.
_cache: dict = {}
_CACHE_TTL_SECONDS = 600  # 10 minutes


def _cache_key(slug: str) -> str:
    return f"dao:{slug}"


async def _get_or_fetch(slug: str) -> dict:
    """Cache-aware fetch — avoids hammering DefiLlama on every request."""
    import time
    key = _cache_key(slug)
    cached = _cache.get(key)
    if cached and (time.time() - cached["ts"]) < _CACHE_TTL_SECONDS:
        return cached["data"]

    raw = await fetch_all_for_dao(slug)
    dao_config = get_dao(slug)
    analysis = analyze_dao(raw, dao_config)
    _cache[key] = {"data": analysis, "ts": time.time()}
    return analysis


# ============================================================
# ROUTES
# ============================================================

@app.get("/api/health")
def health():
    return {"status": "ok", "daos_tracked": len(DAO_REGISTRY)}


@app.get("/api/daos")
def get_daos():
    """List all DAOs the platform tracks."""
    return {"daos": list_daos(), "count": len(DAO_REGISTRY)}


@app.get("/api/dao/{slug}")
async def get_dao_analysis(slug: str, burn_usd: float = Query(default=1_000_000, ge=0)):
    """Full treasury analysis for one DAO."""
    if slug not in DAO_REGISTRY:
        raise HTTPException(404, f"Unknown DAO: {slug}")
    try:
        return await _get_or_fetch(slug)
    except Exception as e:
        raise HTTPException(503, f"Data fetch failed: {str(e)}")


@app.get("/api/compare")
async def compare_all():
    """Side-by-side comparison across all 6 DAOs. Parallel fetch."""
    results = await asyncio.gather(
        *[_get_or_fetch(slug) for slug in DAO_REGISTRY.keys()],
        return_exceptions=True,
    )

    by_slug = {}
    for slug, result in zip(DAO_REGISTRY.keys(), results):
        if not isinstance(result, Exception):
            by_slug[slug] = result

    return {
        "comparison": comparative_summary(by_slug),
        "details": by_slug,
        "errors": [str(r) for r in results if isinstance(r, Exception)],
    }


@app.post("/api/memo/{slug}")
async def memo_for_dao(slug: str):
    """Generate AI treasury memo for a single DAO."""
    if slug not in DAO_REGISTRY:
        raise HTTPException(404, f"Unknown DAO: {slug}")
    analysis = await _get_or_fetch(slug)
    if "error" in analysis:
        raise HTTPException(503, analysis["error"])
    try:
        return generate_memo(analysis)
    except Exception as e:
        raise HTTPException(500, f"Memo generation failed: {str(e)}")


@app.post("/api/memo/comparison")
async def memo_comparison():
    """Generate cross-DAO comparative memo."""
    compare_data = await compare_all()
    try:
        return generate_comparison_memo(compare_data["comparison"])
    except Exception as e:
        raise HTTPException(500, f"Comparison memo failed: {str(e)}")
