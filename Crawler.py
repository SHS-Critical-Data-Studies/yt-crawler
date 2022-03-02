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
import time

EXP_ID = 1
visited_links = browser.run_experiment()

# Save the links retrieved during random walk
filename = f"{EXP_ID}_{time.time()}.txt"
logs.dump(filename, visited_links)

# Retrieve the information of the watched videos
logs_rel = logs.load(filename)

all_comments, all_infos = browser.load_information(logs_rel)
browser.save_dataframes(all_comments, all_infos)
