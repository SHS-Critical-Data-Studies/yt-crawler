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
%load_ext autoreload
%autoreload 2
```

```python
from utils import browser
from utils import logs
import time
```

```python
EXP_ID = 1
visited_links = browser.run_experiment()
```

```python
# Save the links retrieved during random walk
filename = f"{EXP_ID}_{time.time()}.txt"
logs.dump(filename, visited_links)
```

```python
# Retrieve the information of the watched videos
logs_rel = logs.load(filename)
```

```python
all_comments, all_infos = browser.load_information(logs_rel)
browser.save_dataframes(all_comments, all_infos)
```

```python
import pandas as pd
pd.__version__
```

```python

```
