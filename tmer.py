# +
from datetime import datetime, timedelta
from time import sleep

def main(current_time):
    print("Current Time =", current_time)


# -

last_time = ""
while(True):
    current_time = datetime.now().strftime("%H")#:%M:%S")
    if(last_time != current_time):
        if(current_time[:2] == "08" or
           current_time[:2] == "20"):
            main(current_time)
    else:
        sleep(1)
    last_time = current_time
