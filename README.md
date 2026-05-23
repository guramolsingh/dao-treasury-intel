# DAO Treasury Intelligence

> Live on-chain treasury monitoring for major DAOs — composition, concentration risk, runway scenarios, and AI-generated treasury health memos.

**Live demo:** https://dao-treasury-intel.vercel.app
**Built with:** Python · FastAPI · React · Vite · DefiLlama · Etherscan · Claude API

---

## The Problem

Most DAOs treat treasury management as bookkeeping. Composition is tracked in Notion docs, runway is estimated in shared spreadsheets, and concentration risk is rediscovered every bear market when native-token-heavy treasuries collapse in lockstep with the token price.

This platform brings standard institutional treasury analysis to DAOs — the same discipline a CFO would apply to a Series B startup, applied to on-chain treasuries with public data.

## What it does

Tracks 6 major DAOs in real time:

| DAO | Category | Tracked Asset |
|---|---|---|
| Optimism Collective | L2 Rollup | OP |
| Arbitrum DAO | L2 Rollup | ARB |
| Uniswap | DEX | UNI |
| Aave | Lending | AAVE |
| Compound | Lending | COMP |
| Sky (MakerDAO) | Stablecoin | SKY |

For each DAO, computes:

1. **Treasury composition** — full asset breakdown with $ value and % of treasury
2. **Concentration risk** — Herfindahl index, top-3 concentration, diversification rating
3. **Native token exposure** — how vulnerable runway is to a price drawdown
4. **Runway under three scenarios** — bear (−70%), base, bull (+200%)
5. **Upcoming token unlocks** — next 6 vesting events from DefiLlama
6. **AI treasury memo** — Claude generates a research-grade health assessment

Plus a comparison view showing all 6 DAOs side by side.

## Architecture

Three-layer separation:

```
┌─────────────────────────────────────────────────────────────┐
│  Data Sources (free APIs, no keys required)                 │
│  DefiLlama · Etherscan · Snapshot · DeFi Llama Emissions    │
└────────────────────┬────────────────────────────────────────┘
                     │ async fetch
┌────────────────────▼────────────────────────────────────────┐
│  Analysis Layer (Python — deterministic, no AI)             │
│  Concentration · Native exposure · Runway · Comparisons     │
└────────────────────┬────────────────────────────────────────┘
                     │ structured JSON
┌────────────────────▼────────────────────────────────────────┐
│  AI Synthesis Layer (Claude — narrates, never calculates)   │
│  Treasury health memos · Cross-DAO comparative analysis     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Frontend (React + Recharts + Tailwind)                     │
│  Dashboard · Charts · Memos · Comparison view               │
└─────────────────────────────────────────────────────────────┘
```

Claude only interprets pre-computed analysis. All financial math happens in Python. This eliminates AI arithmetic errors — same pattern as production FP&A tooling.

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Data | DefiLlama free API | No key, no rate limits, comprehensive DAO coverage |
| Backend | FastAPI + aiohttp | Async parallel fetching across 6 DAOs |
| Analysis | Pure Python (numpy optional) | Auditable, testable, deterministic |
| AI layer | Claude Sonnet 4.5 | Best-in-class for structured analysis |
| Frontend | React + Vite + Tailwind + Recharts | Fast, polished, easy to ship |
| Hosting | Vercel | Free tier, serverless Python + static React |

## Local development

```bash
git clone https://github.com/guramolsingh/dao-treasury-intel
cd dao-treasury-intel

# Backend
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
uvicorn api.main:app --reload

# Frontend (separate terminal)
npm install
npm run dev
```

Then visit http://localhost:5173.

## Key endpoints

```
GET  /api/daos                 List all tracked DAOs
GET  /api/dao/optimism         Full analysis for Optimism
GET  /api/compare              Side-by-side across all 6 DAOs
POST /api/memo/optimism        AI memo for Optimism
POST /api/memo/comparison      Cross-DAO comparison memo
```

## Methodology

See `docs/methodology.md` for the detailed approach to:
- Herfindahl concentration scoring
- Native token exposure risk thresholds
- Runway adjustment under price scenarios
- Why we use DefiLlama as the canonical source

## Roadmap

- [x] v1: 6 DAOs, treasury + concentration + runway + AI memo
- [ ] v2: Live governance proposals from Snapshot/Tally
- [ ] v3: Historical treasury composition (timeline view)
- [ ] v4: Custom DAO addition (any protocol in DefiLlama)
- [ ] v5: Telegram/Discord bot for treasury alerts

## Why I built this

I work in strategic finance and operations at venture-backed startups. As DAOs mature, the same financial discipline becomes essential — and almost none of them have it. This platform is what I would build if I joined a foundation or protocol on day one. It is also open-source so any DAO operator can fork it for their own needs.

---

Built by [Guramol Singh Pabla](https://github.com/guramolsingh) · MIT License
