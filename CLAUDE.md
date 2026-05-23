# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project goal

DAO Treasury Intelligence brings institutional-grade treasury analysis to major
DAOs (Optimism, Arbitrum, Uniswap, Aave, Compound, Sky). It reads live on-chain
data, computes composition, concentration risk, native-token exposure, and
runway under bear/base/bull scenarios, and produces an AI-written health memo.
The audience is DAO operators, delegates, and researchers — output should read
like a strategic-finance memo, not a crypto dashboard.

## Architecture — four layers

```
Data sources  →  Async fetch  →  Analysis  →  AI synthesis
(DefiLlama,    (aiohttp,       (pure       (Claude narrates
 Etherscan)     parallel)       Python)     pre-computed JSON)
```

1. **Data sources** (`api/data_sources/`) — thin clients over free public APIs.
   No keys, no rate limits to manage.
2. **Async fetch** — every DAO's data is gathered in parallel with `asyncio`
   inside `fetch_all_for_dao`. Never serialize what can be awaited together.
3. **Analysis** (`api/analysis/treasury.py`) — deterministic Python. All
   numbers (Herfindahl, runway, exposure %) are computed here, never by the LLM.
4. **AI synthesis** (`api/ai/memo.py`) — Claude receives structured JSON and
   writes prose. It interprets; it does not calculate.

## Key design decisions

- **Claude narrates, never calculates.** All financial math lives in
  `api/analysis/`. The model is given pre-computed numbers and asked for prose.
  This eliminates arithmetic hallucination and keeps the analysis auditable.
- **DefiLlama is the canonical source.** Free, no key, broad DAO coverage. Add
  other sources (Etherscan, Snapshot) only when DefiLlama lacks the field.
- **In-memory cache with 10-minute TTL.** `api/main.py` keeps a `dict` cache
  keyed by DAO slug; entries expire after 600 seconds. Good enough for a single
  serverless instance. Swap for Vercel KV / Redis if multi-instance.

## File structure

```
api/
  main.py              FastAPI app, routes, cache
  config.py            DAO_REGISTRY — slugs, names, native tokens
  data_sources/
    defillama.py       fetch_all_for_dao — treasury, unlocks, prices
  analysis/
    treasury.py        analyze_dao, comparative_summary
  ai/
    memo.py            generate_memo, generate_comparison_memo
docs/methodology.md    Concentration, exposure, runway formulas
test_analysis.py       Smoke tests for the analysis layer
```

## Code style

- **Async-first Python.** Network I/O uses `aiohttp` and `asyncio.gather`. No
  blocking `requests` calls in request paths.
- **Typed dicts for structured payloads.** Public functions accept and return
  `dict` shapes with explicit type hints; prefer `TypedDict` where the shape is
  stable.
- **Prose docstrings.** Each module and public function opens with a short
  paragraph explaining intent. Skip Args/Returns blocks unless they add info
  beyond the type hints.
- **Minimal comments.** Code should read self-evidently; comment only the
  non-obvious WHY (a workaround, an external quirk, an invariant). No
  decorative banners, no narration of WHAT the next line does.
