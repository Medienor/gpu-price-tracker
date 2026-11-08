"""Runcrate, an AI cloud: public pricing feed behind runcrate.ai/pricing (no key).

Prices: `min_price_hr` per GPU type, the live on-demand price per GPU-hour. Types with no live offers are
skipped (the feed can carry a stale price for an out-of-stock type). H100 and V100 are skipped on purpose:
the feed does not say SXM or PCIe for H100, and V100 comes in two memory sizes that `canon` would merge.
"""
from common import canon, http_json

NAME = "Runcrate"
SKIP = ("H100", "V100")


def fetch():
    prices = []
    for g in http_json("https://www.runcrate.ai/api/gpu-pricing")["gpus"]:
        name = g.get("name") or ""
        if g.get("available_options", 0) < 1 or not g.get("min_price_hr") or any(s in name.upper() for s in SKIP):
            continue
        gpu = canon(name)
        if gpu:
            prices.append((gpu, NAME, "on_demand", float(g["min_price_hr"])))
    return prices, []
