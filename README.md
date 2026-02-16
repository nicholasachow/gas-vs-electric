# Gas vs Electric Break-Even Calculator

CLI tool for PHEV owners to answer: **"Given today's gas price, what's the max electricity rate where charging is still cheaper than driving on gas?"**

Pulls live gas prices from [GasBuddy](https://www.gasbuddy.com) and compares against your configured charging locations.

**Live page:** https://nicholasachow.github.io/gas-vs-electric/

## Setup

```bash
uv sync
```

## Usage

```bash
# Fetch live prices from configured stations
uv run python main.py

# Manual gas price
uv run python main.py 4.00

# Override vehicle stats
uv run python main.py --mpg 45 --empg 3.2

# Check premium fuel
uv run python main.py --fuel premium_gas
```

## Example output

```
  Vehicle: 42.6 MPG / 2.9 mi/kWh
  Fetching live regular_gas prices...

  Costco                credit $4.09
  Diamond Gas & Mart    credit $4.15  cash $4.05

  Cheapest gas: $4.09/gal @ Costco

  Break-even electricity price: $0.278/kWh
  Charge if your rate is below $0.278/kWh

  Location                           Rate     $/mi   vs Gas  Verdict
  ------------------------------  -------  -------  -------  -------
  Downtown Palo Alto              $0.24   $0.0828  -0.0133  Charge — save $0.013/mi
  Downtown Mountain View    $0.25   $0.0862  -0.0098  Charge — save $0.010/mi
  Burlingame Highland Garage      $0.43   $0.1483  +0.0523  Gas — costs $0.052/mi more

  Home charger (Downtown Mountain View): $0.25/kWh
  Gas would need to drop below $3.67/gal to beat charging at home
```

## Configuration

Edit the constants at the top of `main.py`:

**Vehicle stats:**
- `MPG` — gas fuel economy in miles per gallon (default: 42.6)
- `EMPG` — electric efficiency in miles per kWh (default: 2.9)

**Gas stations:**
```python
STATIONS = {
    "diamond": 4027,   # Diamond Gas & Mart, Mountain View
    "costco":  490,    # Costco, Sunnyvale
}
```

To add your own stations, find the station ID from its GasBuddy URL:
`https://www.gasbuddy.com/station/<ID>` — the number at the end is the ID.

**Charging locations:**
```python
CHARGERS = {
    "Downtown Palo Alto":           0.24,
    "Downtown Mountain View": 0.25,
    "Burlingame Highland Garage":    0.43,
}
```

Set a rate to `None` to mark it as unknown — the tool will remind you to go find out the price.

**Fuel type options:** `regular_gas`, `midgrade_gas`, `premium_gas`, `diesel`

## How it works

```
cost_per_mile_gas  = gas_price / MPG
cost_per_mile_elec = elec_rate / EMPG
break_even_rate    = gas_price * EMPG / MPG
```

If your electricity rate is below the break-even rate, charge. Otherwise, drive on gas.

## Deployment

The live page auto-updates every 4 hours via GitHub Actions (`.github/workflows/deploy.yml`). No maintenance needed.

**To make changes:**
1. Edit `main.py` (stations, chargers, vehicle stats)
2. Commit and push
3. The page updates on the next scheduled run, or trigger manually at:
   https://github.com/nicholasachow/gas-vs-electric/actions/workflows/deploy.yml

**If the page stops updating:** GasBuddy may have changed their page structure. The `fetch_price()` function in `main.py` scrapes prices from an embedded `__APOLLO_STATE__` JSON blob — if GasBuddy changes this, the scraper will need updating.

**Files:**
- `main.py` — CLI tool + all config (stations, chargers, vehicle stats)
- `generate_html.py` — generates the static HTML page (imports from `main.py`)
- `.github/workflows/deploy.yml` — GitHub Actions cron + Pages deploy
