# Gas vs Electric Break-Even Calculator

CLI tool for PHEV owners to answer: **"Given today's gas price, what's the max electricity rate where charging is still cheaper than driving on gas?"**

Pulls live gas prices from [GasBuddy](https://www.gasbuddy.com) and calculates the break-even electricity rate.

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

  Costco — 150 Lawrence Station Rd, Sunnyvale
  Credit: $4.09/gal  (updated 2026-02-15)

  Break-even electricity price: $0.278/kWh
  Charge if your rate is below $0.278/kWh

     Elec Rate   $/mi (elec)   $/mi (gas)  Verdict
  ------------  ------------  -----------  -------
  $0.10/kWh     $0.0345/mi    $0.0960/mi  Charge
  $0.15/kWh     $0.0517/mi    $0.0960/mi  Charge
  $0.20/kWh     $0.0690/mi    $0.0960/mi  Charge
  $0.25/kWh     $0.0862/mi    $0.0960/mi  Charge
  $0.30/kWh     $0.1034/mi    $0.0960/mi  Gas    <--
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

**Fuel type options:** `regular_gas`, `midgrade_gas`, `premium_gas`, `diesel`

## How it works

```
cost_per_mile_gas  = gas_price / MPG
cost_per_mile_elec = elec_rate / EMPG
break_even_rate    = gas_price * EMPG / MPG
```

If your electricity rate is below the break-even rate, charge. Otherwise, drive on gas.
