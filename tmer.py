# +
# %load_ext autoreload
# %autoreload 2

from datetime import datetime, timedelta
from time import sleep
from utils import browser
from utils import logs
from threading import Thread
import pandas as pd

NUMBER_EXPERIMENT = 4
ID=0
def worker():
    global ID
    number = ID
    ID += 1
    experiment(number)

def main(number):
    global ID
    ID = 0
    for i in range(number):
        Thread(target = worker).start()
        sleep(120)
    sleep(3600)
        
def experiment(number):
    sleep(10*number)
    filename = f'{datetime.now().strftime("%Y_%m_%d.%H_%M_%S")}.{number}'
    visited_links, all_comments, all_infos, home_video = browser.run_experiment("firefox")
    
    # Save the links retrieved during random walk
    logs.dump(f"{filename}.txt", visited_links)
    browser.save_dataframes(all_comments, all_infos, home_video, path=f'data/{filename}.')


# -

last_time = ""
while(True):
    current_time = datetime.now().strftime("%H")
    if(last_time != current_time):
        if(current_time[:2] == "08" or
           current_time[:2] == "20"):
            main(NUMBER_EXPERIMENT)
    else:
        if(abs(int(current_time)%12 - 8) > 1):
            sleep(3600)
        elif(int(datetime.now().strftime("%M")) - 58 < 0):
            sleep(60)
        else:
            sleep(1)
    last_time = current_time

main(4)
