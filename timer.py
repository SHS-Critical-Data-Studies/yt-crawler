# +
# %load_ext autoreload
# %autoreload 2

from datetime import datetime, timedelta
from time import sleep
from utils import browser
from utils import logs
from threading import Thread
import pandas as pd
import sys

browser_name = "firefox"
version = 'P5'

def experiment(number, theme, url):
    sleep(60*number)
    filename = f'{datetime.now().strftime("%Y_%m_%d.%H_%M_%S")}.{number}'
    watched_videos, all_comments, all_infos, home_video, themes = browser.run_experiment(filename, browser_name=browser_name, version=version, theme=theme, url=url)
    logs.dump(f"{filename}.txt", watched_videos)


# +
start_time = [ "08:00", "12:45", "17:30", "22:15", "03:00" ]
start_time_ct = [start_time[i].split(':') for i in range(len(start_time))]
start_time_ct = [(int(start_time_ct[i][0]) * 60 + int(start_time_ct[i][1])) * 60 for i in range(len(start_time))]

if __name__ == "__main__":
    try:
        NUMBER_EXPERIMENT = int(sys.argv[1])
        print(NUMBER_EXPERIMENT)
    except:
        NUMBER_EXPERIMENT = 0
    last_time = ""
    theme = []
    url = []
    while(True):
        current_time = datetime.now().strftime("%H:%M")
        if(last_time != current_time):
            if(current_time in start_time):
                if(len(theme) == 0):
                    theme = browser.get_theme(browser_name=browser_name, nb=len(start_time)+2)
                if(len(url) == 0):
                    url = browser.get_starting_videos_diff_magnitude(theme[0], browser_name=browser_name)
                experiment(NUMBER_EXPERIMENT, theme[0], url[0])
                url.pop(0)
                if(len(url) == 0):
                    theme.pop(0)
        else:
            split = current_time.split(':')
            ct = (int(split[0]) * 60 + int(split[1])) * 60
            dt = min(start_time_ct[i] - ct if(start_time_ct[i] - ct > 0) else start_time_ct[i] - ct + (24*60*60) for i in range(len(start_time))) - 60
            sleep(max(1, dt))
        last_time = current_time
# -


