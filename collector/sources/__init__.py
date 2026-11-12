from . import (akash, aws, azure, clore, coreweave, crusoe, cudo, digitalocean, hyperbolic, hyperstack, ionet,
               jarvislabs, lambdalabs, lium, nebius, nosana, oracle, ovh, runcrate, runpod, salad, scaleway, shadeform,
               spheron, together, vast, verda)

# Every source module; collect.py runs them in parallel. Vast.ai is the slow one (rate-limited paging).
ALL = [
    vast, clore, lium,                                    # open marketplaces
    akash, ionet, nosana, salad,                          # decentralized networks
    runpod, verda, hyperbolic, cudo, scaleway, ovh, runcrate,  # GPU clouds (APIs)
    lambdalabs, coreweave, nebius, together,              # GPU clouds (pricing pages)
    crusoe, hyperstack, digitalocean, jarvislabs,
    spheron, shadeform,                                   # aggregators
    aws, azure, oracle,                                   # hyperscalers
]
