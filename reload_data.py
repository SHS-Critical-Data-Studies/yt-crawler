from utils import browser
import sys

if __name__ == "__main__":
    try:
        path = int(sys.argv[1])
    except:
        path = 'data'
    browser.reload_data(path)