import argparse
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

MPG = 42.6   # gas fuel economy (miles per gallon)
EMPG = 2.9   # electric efficiency (miles per kWh)

STATIONS = {
    "diamond": 4027,   # Diamond Gas & Mart, 789 E Evelyn Ave, Mountain View
    "costco":  490,    # Costco, 150 Lawrence Station Rd, Sunnyvale
}

FUEL_TYPE = "regular_gas"


def fetch_price(station_id: int) -> dict | None:
    """Scrape live gas prices from a GasBuddy station page."""
    url = f"https://www.gasbuddy.com/station/{station_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for script in soup.find_all("script"):
        text = script.string or ""
        if "__APOLLO_STATE__" not in text:
            continue
        match = re.search(
            r"window\.__APOLLO_STATE__\s*=\s*(\{.*?\});", text, re.DOTALL
        )
        if not match:
            continue
        data = json.loads(match.group(1))
        station_key = f"Station:{station_id}"
        if station_key not in data:
            return None
        station = data[station_key]
        return {
            "name": station.get("name"),
            "address": station.get("address", {}).get("line1"),
            "city": station.get("address", {}).get("locality"),
            "prices": {
                p["fuelProduct"]: {
                    "credit": (p.get("credit") or {}).get("price"),
                    "cash": (p.get("cash") or {}).get("price"),
                    "updated": (p.get("credit") or {}).get("postedTime"),
                }
                for p in station.get("prices", [])
            },
        }
    return None


def print_breakeven(gas_price: float, mpg: float, empg: float):
    cost_per_mile_gas = gas_price / mpg
    cutoff = gas_price * empg / mpg

    print(f"\n  Break-even electricity price: ${cutoff:.3f}/kWh")
    print(f"  Charge if your rate is below ${cutoff:.3f}/kWh\n")

    print(f"  {'Elec Rate':>12}  {'$/mi (elec)':>12}  {'$/mi (gas)':>11}  Verdict")
    print(f"  {'-'*12}  {'-'*12}  {'-'*11}  {'-'*7}")
    for rate in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]:
        cost_elec = rate / empg
        verdict = "Charge" if rate < cutoff else "Gas"
        marker = " <--" if abs(rate - cutoff) < 0.025 else ""
        print(f"  ${rate:.2f}/kWh     ${cost_elec:.4f}/mi    ${cost_per_mile_gas:.4f}/mi  {verdict}{marker}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Gas vs Electric break-even calculator"
    )
    parser.add_argument(
        "gas_price", nargs="?", type=float, default=None,
        help="gas price in $/gal (omit to fetch live from GasBuddy)",
    )
    parser.add_argument("--mpg", type=float, default=MPG)
    parser.add_argument("--empg", type=float, default=EMPG)
    parser.add_argument(
        "--fuel", default=FUEL_TYPE,
        help=f"fuel type: regular_gas, midgrade_gas, premium_gas, diesel (default: {FUEL_TYPE})",
    )
    args = parser.parse_args()

    print(f"\n  Vehicle: {args.mpg} MPG / {args.empg} mi/kWh")

    if args.gas_price is not None:
        print(f"  Gas price: ${args.gas_price:.3f}/gal (manual)")
        print_breakeven(args.gas_price, args.mpg, args.empg)
        return

    # Fetch live prices from all configured stations
    print(f"  Fetching live {args.fuel} prices...\n")
    results = []
    for label, sid in STATIONS.items():
        try:
            info = fetch_price(sid)
        except Exception as e:
            print(f"  [{label}] fetch failed: {e}")
            continue
        if not info or args.fuel not in info["prices"]:
            print(f"  [{label}] no {args.fuel} price available")
            continue
        price_info = info["prices"][args.fuel]
        credit = price_info["credit"]
        if credit is None:
            continue
        cash = price_info.get("cash")
        results.append((credit, cash, info))

    if not results:
        print("  No live prices found. Pass a price manually:")
        print("    uv run python main.py 4.00")
        sys.exit(1)

    # Show all station prices
    results.sort(key=lambda r: r[0])
    for credit, cash, info in results:
        cash_str = f"  cash ${cash:.2f}" if cash else ""
        print(f"  {info['name']:20s}  credit ${credit:.2f}{cash_str}")

    # Break-even based on cheapest credit price
    cheapest_credit, _, cheapest_info = results[0]
    print(f"\n  Cheapest gas: ${cheapest_credit:.2f}/gal @ {cheapest_info['name']}")
    print_breakeven(cheapest_credit, args.mpg, args.empg)


if __name__ == "__main__":
    main()
