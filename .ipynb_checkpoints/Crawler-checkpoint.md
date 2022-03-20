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
#all_comments, all_infos = browser.load_information(logs_rel)
filename = datetime.now().strftime("%Y_%m_%d.%H_%M_%S")
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
