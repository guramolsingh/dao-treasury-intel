"""
DAO Registry — the 6 protocols this platform monitors.

Each entry maps to:
- DefiLlama slug (for treasury composition + TVL data)
- Snapshot space (for off-chain governance)
- Tally governor (for on-chain governance, when applicable)
- Category (for filtering and comparison views)

Start with these 6 because they have:
1. Publicly trackable treasuries (multi-sigs or DAO-controlled)
2. Active governance (Snapshot or Tally)
3. Token unlocks visible on DefiLlama
4. Distinct DAO archetypes (L2, DEX, lending, stablecoin)
"""

DAO_REGISTRY = {
    "optimism": {
        "display_name": "Optimism Collective",
        "ticker": "OP",
        "category": "L2 Rollup",
        "defillama_slug": "optimism",
        "defillama_treasury_slug": "optimism",
        "snapshot_space": "opcollective.eth",
        "tally_org": "optimism",
        "founded": 2022,
        "description": "Ethereum L2 with the Optimism Collective governance structure.",
    },
    "arbitrum": {
        "display_name": "Arbitrum DAO",
        "ticker": "ARB",
        "category": "L2 Rollup",
        "defillama_slug": "arbitrum",
        "defillama_treasury_slug": "arbitrum",
        "snapshot_space": "arbitrumfoundation.eth",
        "tally_org": "arbitrum",
        "founded": 2023,
        "description": "Largest L2 by TVL, governed by ARB holders via Tally.",
    },
    "uniswap": {
        "display_name": "Uniswap",
        "ticker": "UNI",
        "category": "DEX",
        "defillama_slug": "uniswap-v3",
        "defillama_treasury_slug": "uniswap",
        "snapshot_space": "uniswapgovernance.eth",
        "tally_org": "uniswap",
        "founded": 2018,
        "description": "Largest DEX. Treasury denominated heavily in UNI.",
    },
    "aave": {
        "display_name": "Aave",
        "ticker": "AAVE",
        "category": "Lending",
        "defillama_slug": "aave-v3",
        "defillama_treasury_slug": "aave",
        "snapshot_space": "aave.eth",
        "tally_org": "aave",
        "founded": 2020,
        "description": "Largest lending protocol. Treasury managed by Aave Companies.",
    },
    "compound": {
        "display_name": "Compound",
        "ticker": "COMP",
        "category": "Lending",
        "defillama_slug": "compound-v3",
        "defillama_treasury_slug": "compound",
        "snapshot_space": "comp-vote.eth",
        "tally_org": "compound",
        "founded": 2018,
        "description": "Original DeFi DAO. Notable for early experiments in governance.",
    },
    "makerdao": {
        "display_name": "Sky (MakerDAO)",
        "ticker": "SKY",
        "category": "Stablecoin",
        "defillama_slug": "makerdao",
        "defillama_treasury_slug": "makerdao",
        "snapshot_space": "makerdao.eth",
        "tally_org": "makerdao",
        "founded": 2017,
        "description": "Oldest DeFi DAO. Issues DAI/USDS, sophisticated treasury operations.",
    },
}


def get_dao(slug: str) -> dict:
    """Lookup a DAO by slug. Raises KeyError if not found."""
    if slug not in DAO_REGISTRY:
        raise KeyError(f"Unknown DAO: {slug}. Available: {list(DAO_REGISTRY.keys())}")
    return DAO_REGISTRY[slug]


def list_daos() -> list[dict]:
    """Return all DAOs as a list (for API responses)."""
    return [{"slug": k, **v} for k, v in DAO_REGISTRY.items()]
