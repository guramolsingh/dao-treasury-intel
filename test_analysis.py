"""
Smoke test for the analysis module.
Runs with realistic mock data — proves the math works before wiring real APIs.
"""
import sys
sys.path.insert(0, '.')

from api.config import get_dao
from api.analysis.treasury import analyze_dao

# Mock treasury data that approximates Optimism's actual composition
mock_optimism = {
    "treasury": {
        "name": "Optimism",
        "total_usd": 850_000_000,
        "tokens": [
            {"symbol": "OP", "usd_value": 595_000_000, "pct_of_treasury": 70.0},
            {"symbol": "USDC", "usd_value": 170_000_000, "pct_of_treasury": 20.0},
            {"symbol": "ETH", "usd_value": 51_000_000, "pct_of_treasury": 6.0},
            {"symbol": "DAI", "usd_value": 34_000_000, "pct_of_treasury": 4.0},
        ],
        "chain_breakdown": {"ethereum": 425_000_000, "optimism": 425_000_000},
    },
    "tvl": {
        "current_tvl": 5_400_000_000,
        "tvl_30d_ago": 5_100_000_000,
        "tvl_change_pct_30d": 5.9,
    },
    "unlocks": [
        {"timestamp": 1735689600, "tokens_unlocked": 24_160_000, "description": "Monthly unlock"},
    ],
}

optimism_config = get_dao("optimism")
result = analyze_dao(mock_optimism, optimism_config, monthly_burn_usd=8_000_000)

print(f"=== {result['dao']} Treasury Analysis ===\n")

print(f"Treasury total      : ${result['treasury']['total_usd']:,.0f}")
print(f"TVL                 : ${result['tvl']['current_tvl']:,.0f}")
print(f"Treasury/TVL        : {result['treasury']['total_usd']/result['tvl']['current_tvl']*100:.1f}%\n")

print("=== Concentration Risk ===")
for k, v in result['concentration'].items():
    print(f"  {k:20s}: {v}")

print("\n=== Native Token Exposure ===")
for k, v in result['native_exposure'].items():
    if isinstance(v, (int, float)) and k != 'native_usd':
        print(f"  {k:20s}: {v}%")
    else:
        print(f"  {k:20s}: {v}")

print(f"\n=== Runway (assuming ${result['monthly_burn_assumption']:,}/mo burn) ===")
for scenario, data in result['runway'].items():
    print(f"  {scenario:5s} (×{data['price_multiplier']}): {data['runway_months']:>6} months  |  Adjusted treasury: ${data['adjusted_treasury']:,.0f}")
