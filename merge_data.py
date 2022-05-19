from utils import browser

if __name__ == "__main__":
    try:
        path = int(sys.argv[1])
    except:
        path = 'data'
    browser.merge_data(path)