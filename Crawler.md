---
jupyter:
  jupytext:
    formats: ipynb,md,py:light
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.13.7
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
from os import listdir
from os.path import isfile, join

import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import time
from datetime import datetime, timedelta
import pandas as pd
from selenium import webdriver
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language
from random import randrange
import numpy as np

MAX_VIDEO_POSITION = 8
WATCH_TIME_VIDEOS = 60 * 25
MAX_TOTAL_TIME = 60 * 60 * 10
MAX_VIDEOS = 30
USE_TIME = True
TIME_BETWEEN_SCROLL = 0.5
NB_COMMENTS = 100
LANGUAGE_TO_USE = 'en'
VIDEO_TIME_OFFSET = 30

encoding = 'utf-8'
compression = 'bz2'
mypath = 'data\\P3'
f = ''

pd.read_csv(join(mypath, 'tmp', f), compression=compression,encoding=encoding)
```

```python
%load_ext autoreload
%autoreload 2
```

```python
from utils import browser
from utils import logs
from datetime import datetime
```

```python
EXP_ID = 1
visited_links, all_comments, all_infos = browser.run_experiment()
```

```python
# Save the links retrieved during random walk
filename = datetime.now().strftime("%Y_%m_%d.%H_%M_%S")
logs.dump(f"{filename}.txt", visited_links)
```

```python
# Retrieve the information of the watched videos
logs_rel = logs.load(f"{filename}.txt")
```

```python
all_comments, all_infos = browser.load_information(logs_rel)
browser.save_dataframes(all_comments, all_infos, path=f'data/{filename}.')
```

```python
import pandas as pd
pd.__version__
```

```python
print(all_comments.head(10))
print('-----------------------------------------------------')
print(all_infos.head(10))
```
