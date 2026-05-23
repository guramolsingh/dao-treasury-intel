# Build Plan — 6 Weekend Roadmap

Realistic, sequenced plan to ship from empty repo to deployed live product.

Note: This is one weekend longer than the Tokenomics Engine. The extra weekend is for the Web3 learning curve — reading on-chain data, understanding DAO treasury structures. Don't skip it.

---

## Weekend 0 (preparation, before any code)

**Goal:** Understand the domain well enough to build something a DAO operator would respect.

Tasks:
- [ ] Read DefiLlama's documentation: https://docs.llama.fi/api
- [ ] Manually look up the treasury page for each of the 6 DAOs on DefiLlama
- [ ] Read one recent governance proposal from Optimism, Arbitrum, and Uniswap on Snapshot
- [ ] Read Hasu's "Open Problems in DAO Governance" essay (or any 2024+ piece on DAO treasury management)
- [ ] Note: how do real DAO operators talk about treasury health? What terminology do they use?

**Deliverable:** A one-page notes doc on what real DAO treasury operators care about. This shapes your priorities.

---

## Weekend 1 — Backend foundation

**Goal:** Python backend that fetches live data from DefiLlama for one DAO and runs the analysis pipeline.

Tasks:
- [x] Project structure (`/api`, `/src`, root configs)
- [x] DAO registry config (6 protocols)
- [x] DefiLlama client (`fetch_treasury`, `fetch_protocol_tvl`, `fetch_upcoming_unlocks`)
- [x] Analysis module (concentration, native exposure, runway)
- [ ] Verify the DefiLlama treasury endpoint returns real data for each of the 6 DAOs
- [ ] Add error handling for missing/unavailable data per DAO
- [ ] Write unit tests for the analysis functions (use `pytest`)

**Deliverable:** `curl localhost:8000/api/dao/optimism` returns valid analysis JSON.

---

## Weekend 2 — Full backend + AI memo

**Goal:** All 6 DAOs working, comparison endpoint, AI memo generation.

Tasks:
- [x] Comparison endpoint (`/api/compare`) with parallel fetching
- [x] AI memo module with Claude integration
- [x] Comparative memo generator
- [ ] In-memory caching (10-minute TTL) to avoid hammering DefiLlama
- [ ] Test memo quality — does Claude produce a memo that sounds like Delphi/Messari analysts? If not, refine the prompt.
- [ ] Add `/api/memo/comparison` endpoint
- [ ] Verify all 6 DAOs return valid data

**Deliverable:** All endpoints working end to end with real data.

---

## Weekend 3 — Frontend dashboard

**Goal:** A React UI that shows one DAO's full analysis with charts.

Tasks:
- [ ] Scaffold Vite + React + Tailwind + shadcn/ui
- [ ] Build `<DaoSelector />` — switches between the 6 DAOs
- [ ] Build `<TreasuryComposition />` — donut chart of asset breakdown
- [ ] Build `<RunwayScenarios />` — three scenario cards (bear/base/bull)
- [ ] Build `<ConcentrationCard />` — Herfindahl + diversification rating
- [ ] Build `<UpcomingUnlocks />` — timeline of next 6 unlock events
- [ ] Wire all to `/api/dao/{slug}` endpoint

**Deliverable:** Single-DAO dashboard working with live data.

---

## Weekend 4 — Comparison view + AI memo display

**Goal:** The cross-DAO comparison view and the AI memo render beautifully.

Tasks:
- [ ] Build `<ComparisonTable />` — sortable table across all 6 DAOs
- [ ] Build `<ComparisonCharts />` — side-by-side treasury size, native exposure heatmap
- [ ] Build `<ExecutiveMemo />` — calls `/api/memo/{slug}`, displays with editorial typography
- [ ] Add loading states (skeleton loaders during fetch and memo generation)
- [ ] Mobile-responsive layout
- [ ] Dark mode polish

**Deliverable:** All views look production-grade.

---

## Weekend 5 — Polish, deploy, document

**Goal:** Live on Vercel, polished README, ready for resume.

Tasks:
- [ ] Deploy to Vercel — set `ANTHROPIC_API_KEY` in environment variables
- [ ] Verify production endpoints work
- [ ] Write methodology doc (`docs/methodology.md`)
- [ ] Add hero screenshot + 30s loom video to README
- [ ] MIT license, contributor guidelines
- [ ] Pin the repo on your GitHub profile
- [ ] Add the project to your resume

**Deliverable:** Public, live, ready to link from job applications.

---

## Weekend 6 — Distribution

**Goal:** Get the project in front of the right people.

Tasks:
- [ ] Write a LinkedIn post — what you built, why, who it's useful for
- [ ] Submit to crypto governance Discord/Telegram groups (Optimism gov, Arbitrum forums)
- [ ] Tweet at DAO ops people who might find it useful
- [ ] Post in r/CryptoCurrency or r/ethfinance if quality is high enough
- [ ] Cold-email 5 DAO foundations: "I built this for fun, would love your feedback. Are you hiring?"

This is the most important weekend. The project only matters if recruiters see it.

**Deliverable:** Project has shipped, has eyes on it, and you have at least one warm conversation started.

---

## Resume bullet (use after Weekend 5)

> **DAO Treasury Intelligence** | Open-source on-chain treasury platform | Python, FastAPI, React, DefiLlama, Etherscan, Claude API
> dao-treasury-intel.vercel.app | github.com/guramolsingh/dao-treasury-intel
>
> - Built and deployed an on-chain treasury monitoring platform tracking $4B+ in combined assets across 6 major DAOs (Optimism, Arbitrum, Uniswap, Aave, Compound, MakerDAO), with live composition, concentration risk scoring, and three-scenario runway analysis.
> - Architected a three-layer system separating async data fetching, deterministic financial analysis, and AI-generated research memos, eliminating AI arithmetic errors while producing institutional-grade treasury health assessments under 10 seconds.
