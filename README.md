# GPU Price Tracker

Tracks hourly GPU rental prices (USD per GPU-hour) and demand across ~25 sources, with a
focus on how the flagship GPUs (B300, B200, H200, H100) are moving. It runs free, with no server
and no database: GitHub Actions collects a snapshot every hour, commits it to this repo and
redeploys the static site to GitHub Pages.

```
GitHub Actions (hourly cron)
  └─ collector/collect.py   runs every module in collector/sources/ in parallel
                            ─► data/prices/YYYY/MM/DD.csv   ts, gpu, source, market, min, median, n
                            ─► data/demand/YYYY/MM/DD.csv   ts, gpu, source, metric, value
  └─ collector/build.py     snapshots ─► site/data/summary.json + site/data/gpu/*.json
  └─ deploy site/ to GitHub Pages
```

## What the site shows

- **Flagship cards**: typical price per GPU-hour, cheapest offer, 24h/7d/30d change, trend, demand.
- **Outlook**: where on-demand prices are heading, from three independent signals:
  - *market-implied*: commitment prices (1 month … 5 years) turned into the average price they imply
    for each future period, like forward rates from a yield curve (includes a certainty discount);
  - *generation analog*: older GPUs' month-by-month list-price path, applied from the same age;
  - *announced* future price lists, and a *live trend* (robust 30-day trend, after 14 days of data).
  Plus the commitment curve per source and generation age curves.
- **Price trend**: flagship GPUs on one chart, as % change since the start of the range (or $/hr).
- **Neoclouds vs the open market**: separate price indices for neoclouds, marketplaces and
  hyperscalers, and the neocloud premium over the open market (falling = commoditizing).
- **Price moves**: a feed of list-price changes, new and withdrawn offers at neoclouds and
  hyperscalers, plus announced future prices (e.g. Crusoe's next price list).
- **Generation shift**: share of listed data-center GPUs that are Blackwell / Hopper / Ampere, and
  price per dense BF16 PFLOP-hour (or as % of B200's price).
- **Market tightness**: 0–100 per GPU (rented share, share of sources sold out, 100 − spot discount),
  and the spot discount itself.
- **Demand**: share of listed GPUs that are rented right now, utilization over time, listed vs rented
  GPU counts, "hardest to get" (share of the time sources were sold out), and a heatmap of either.
- **Where it's cheapest**: every source's price for every GPU on one log-scale strip plot.
- **By source**: one GPU's price history at each source.

How the numbers are made:
- **Typical price** = the lower median of the sources' median prices right now.
- **Trend and changes** use a *chained index*: every hour, each source is compared only with its own
  previous price and the index moves by the average change. Sources appearing, disappearing or
  failing for an hour therefore never cause jumps.
- **Utilization** = rented ÷ listed GPUs, summed over marketplaces that publish both counts
  (Vast.ai, Clore.ai, Lium, Akash, io.net, Nosana).
- **Sold out** = a source had no free GPUs of that model (rented ≥ listed) or reported no stock
  (Scaleway "shortage"). "Hardest to get" averages this over every source-hour in the range.
  RunPod only counts when it reports a stock level; it often reports none to anonymous requests.
- A source priced below a quarter of the other sources' median is treated as a stale listing.

## Sources

| Kind | Source | Prices | Demand signal |
|---|---|---|---|
| Marketplace | Vast.ai | every offer, on-demand + spot (min bid) | rented share per machine |
| Marketplace | Clore.ai | every available server | rented vs listed servers |
| Marketplace | Lium (Bittensor SN51) | per GPU class | rental rate |
| Decentralized | Akash | provider bids | leased vs total GPUs |
| Decentralized | io.net | per hardware type | hired vs total |
| Decentralized | Nosana | per market | running vs idle nodes |
| Decentralized | Salad | — | utilization % (consumer GPUs) |
| GPU cloud | RunPod (Community, Secure) | list prices | stock level |
| GPU cloud | Verda (DataCrunch), Hyperbolic, Cudo, Runcrate | API | — |
| GPU cloud | Scaleway, OVHcloud | public catalogs (EUR → USD at ECB rate) | Scaleway: zone availability |
| GPU cloud | Lambda, CoreWeave, Nebius, Together AI, Crusoe, Hyperstack, DigitalOcean, Jarvislabs | pricing pages (on-demand, spot where listed) | — |
| Aggregator | Spheron | resold offers, on-demand + spot | — |
| Aggregator | Shadeform (needs free key) | ~18 clouds | share of instance types in stock |
| Hyperscaler | AWS | spot (all regions) + on-demand | Spot Advisor interruptions, discount |
| Hyperscaler | Azure | spot + pay-as-you-go | — |
| Hyperscaler | Oracle Cloud | list price | — |

All public, no login. Shadeform's API docs require a key: get a free one and add it as the
`SHADEFORM_API_KEY` repository secret, otherwise that source is skipped. Spheron accepts an
optional `SPHERON_API_KEY`. The pricing-page scrapers fail loudly (and are skipped for that hour)
if a page changes layout, so check the Actions log now and then.

Not available without an account: SF Compute's order book (would add real bid/ask depth),
TensorDock, Prime Intellect, Lambda/Hyperstack availability APIs. GCP spot prices exist on
cloud.google.com/spot-vms/pricing but the page is ~18 MB, so it isn't scraped.

## Run locally

Needs Python 3.10+ and nothing else.

```bash
python collector/collect.py              # one snapshot, ~4 minutes (Vast.ai is rate-limited)
python collector/collect.py --only aws,lium   # just some sources
python collector/build.py                # writes site/data/
python -m http.server 8000 -d site
```

## Deploy (free, on GitHub)

1. Push this folder to a new GitHub repository (public repos get unlimited Actions minutes).
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. Optional: add `SHADEFORM_API_KEY` under **Settings → Secrets and variables → Actions**.
4. In **Actions**, open **Collect GPU prices** and click **Run workflow** once. After that it runs
   every hour, and the site is at `https://<user>.github.io/<repo>/`.

GitHub's scheduled runs can be late or skipped when GitHub is busy, so the workflow is scheduled
four times an hour: the first run each hour collects, the others see the snapshot and stop
(`collect.py --skip-if-fresh`). Remaining gaps show as breaks in the charts. Collecting and
publishing are separate jobs, so a GitHub Pages hiccup never loses a snapshot; the next run
publishes it. On a public repo GitHub may pause schedules after 60 days without activity — re-enable
the workflow in the Actions tab if that happens.

## Price history from the Internet Archive

`collector/backfill/*_history.py` rebuild years of neocloud list prices from archived snapshots of
providers' pricing pages (Wayback Machine, one snapshot per month) into `data/backfill/*.csv`
(`date,gpu,source,market,price,url` — every row links to the snapshot it came from). They run once,
not hourly; rerun one to refresh it, e.g. `python collector/backfill/lambda_history.py`. The build merges
this history with the live data for the generation age curves and the analog projection.

## Adding a source

Create `collector/sources/<name>.py` with `NAME` and `fetch()` returning `(prices, demand)` (see
`collector/common.py` for the format and the `canon()` GPU-name mapper), add it to
`collector/sources/__init__.py`, and add display info to `SOURCES` in `collector/build.py`.
