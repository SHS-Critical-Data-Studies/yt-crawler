# ---
# jupyter:
#   jupytext:
#     formats: ipynb,md,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %load_ext autoreload
# %autoreload 2

from utils import browser
from utils import logs
from datetime import datetime

EXP_ID = 1
visited_links, all_comments, all_infos = browser.run_experiment()

# Save the links retrieved during random walk
filename = datetime.now().strftime("%Y_%m_%d.%H_%M_%S")
logs.dump(f"{filename}.txt", visited_links)

# Retrieve the information of the watched videos
logs_rel = logs.load(f"{filename}.txt")

all_comments, all_infos = browser.load_information(logs_rel)
browser.save_dataframes(all_comments, all_infos, path=f'data/{filename}.')

import pandas as pd
pd.__version__

print(all_comments.head(10))
print('-----------------------------------------------------')
print(all_infos.head(10))
