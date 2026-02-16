"""Generate a static HTML page with current gas vs electric comparison."""

from datetime import datetime, timezone

from main import CHARGERS, EMPG, FUEL_TYPE, HOME_CHARGER, MPG, STATIONS, fetch_price


def build_html() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Fetch gas prices
    gas_results = []
    errors = []
    for label, sid in STATIONS.items():
        try:
            info = fetch_price(sid)
            if info and FUEL_TYPE in info["prices"]:
                credit = info["prices"][FUEL_TYPE]["credit"]
                cash = info["prices"][FUEL_TYPE].get("cash")
                if credit is not None:
                    gas_results.append((credit, cash, info))
        except Exception as e:
            errors.append(f"{label}: {e}")

    if not gas_results:
        return f"<html><body><h1>Failed to fetch gas prices</h1><p>{errors}</p></body></html>"

    gas_results.sort(key=lambda r: r[0])
    cheapest_credit, _, cheapest_info = gas_results[0]
    cost_per_mile_gas = cheapest_credit / MPG
    cutoff = cheapest_credit * EMPG / MPG

    # Build gas station rows
    gas_rows = ""
    for credit, cash, info in gas_results:
        cash_str = f"${cash:.2f}" if cash else "—"
        gas_rows += f"<tr><td>{info['name']}</td><td>{info['address']}, {info['city']}</td><td>${credit:.2f}</td><td>{cash_str}</td></tr>\n"

    # Build charger rows
    charger_rows = ""
    for name, rate in CHARGERS.items():
        if rate is None:
            charger_rows += f'<tr class="unknown"><td>{name}</td><td>???</td><td>—</td><td>—</td><td>GO FIND OUT!</td></tr>\n'
            continue
        cost_elec = rate / EMPG
        diff = cost_elec - cost_per_mile_gas
        if diff < -0.001:
            verdict = f"Charge — save ${abs(diff):.3f}/mi"
            cls = "charge"
        elif diff > 0.001:
            verdict = f"Gas — costs ${diff:.3f}/mi more"
            cls = "gas"
        else:
            verdict = "Basically equal"
            cls = "equal"
        charger_rows += f'<tr class="{cls}"><td>{name}</td><td>${rate:.2f}</td><td>${cost_elec:.4f}</td><td>{diff:+.4f}</td><td>{verdict}</td></tr>\n'

    # Home charger info
    home_rate = CHARGERS.get(HOME_CHARGER)
    home_section = ""
    if home_rate is not None:
        gas_to_beat = home_rate * MPG / EMPG
        home_section = f"""
        <div class="home-info">
            Gas would need to drop below <strong>${gas_to_beat:.2f}/gal</strong> to beat charging at home
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gas vs Electric</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, system-ui, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; max-width: 600px; margin: 0 auto; }}
  h1 {{ font-size: 1.3em; margin-bottom: 4px; }}
  h2 {{ font-size: 1.1em; margin: 20px 0 8px; color: #8888cc; }}
  .updated {{ color: #888; font-size: 0.85em; margin-bottom: 16px; }}
  .hero {{ background: #16213e; border-radius: 12px; padding: 16px; margin: 16px 0; text-align: center; }}
  .hero .price {{ font-size: 2em; font-weight: bold; color: #4ecca3; }}
  .hero .label {{ font-size: 0.9em; color: #aaa; margin-top: 4px; }}
  .vehicle {{ color: #888; font-size: 0.85em; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
  th {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #333; color: #8888cc; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #222; }}
  tr.charge td {{ color: #4ecca3; }}
  tr.gas td {{ color: #e74c3c; }}
  tr.equal td {{ color: #f39c12; }}
  tr.unknown td {{ color: #f39c12; font-style: italic; }}
  .home-info {{ background: #16213e; border-radius: 8px; padding: 12px; margin-top: 16px; font-size: 0.9em; text-align: center; }}
  .home-info strong {{ color: #4ecca3; }}
</style>
</head>
<body>
<h1>Gas vs Electric</h1>
<div class="vehicle">{MPG} MPG / {EMPG} mi/kWh</div>
<div class="updated">Updated {now}</div>

<div class="hero">
  <div class="label">Cheapest gas: {cheapest_info['name']}</div>
  <div class="price">${cheapest_credit:.2f}/gal</div>
  <div class="label">Break-even electricity rate</div>
  <div class="price">${cutoff:.3f}/kWh</div>
</div>

<h2>Gas Stations</h2>
<table>
<tr><th>Station</th><th>Location</th><th>Credit</th><th>Cash</th></tr>
{gas_rows}</table>

<h2>Charging Locations</h2>
<table>
<tr><th>Location</th><th>Rate</th><th>$/mi</th><th>vs Gas</th><th>Verdict</th></tr>
{charger_rows}</table>
{home_section}
</body>
</html>"""


if __name__ == "__main__":
    print(build_html())
