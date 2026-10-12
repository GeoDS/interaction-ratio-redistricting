import os
import random
# from help():
# get(self, key, default=None)
 #       D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.

# seed = os.environ.get("GERRYCHAIN_RANDOM_SEED", 2018)
# seed = os.environ.get("GERRYCHAIN_RANDOM_SEED", 1993)
seed = os.environ.get("GERRYCHAIN_RANDOM_SEED", 2018)
print(f'Seed value set in random.py == {seed}')
random.seed(seed)
