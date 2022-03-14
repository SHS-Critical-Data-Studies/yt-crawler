import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
from selenium import webdriver
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('language_detector', last=True)



FIRST_VIDEO_POSITION = 0
NEXT_VIDEO_POSITION = 0
WATCH_TIME_VIDEOS = 60 * 25
MAX_TOTAL_TIME = 60 * 60 * 10
MAX_VIDEOS = 30
USE_TIME = True
TIME_BETWEEN_SCROLL = 0.5
NB_COMMENTS = 100
LANGUAGE_TO_USE = 'en'
VIDEO_TIME_OFFSET = 10

ENCODING = 'utf-8'
COMPRESSION = 'bz2'

DATA_PATH = 'data/'
COMMENTS_DF_PATH = "comments.csv.bz2"
VIDEOS_DF_PATH = "infos.csv.bz2"



def start_browser(url="https://www.youtube.com"):
    """
    Start and return the browser loaded at a given url
    
    :param url:
    :return: the selenium browser instance
    """
    env_key = "YTCRAWLER_BROWSER"
    path = os.getcwd()

    browser = os.environ.get(env_key)
    if(browser == None):
        print("No browser defined: ")
        browser = input()
        browser = os.environ[env_key] = browser
    else:
        print("Defined browser: {}", browser)

    if browser == "chrome":
        from webdriver_manager.chrome import ChromeDriverManager   
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--lang=en")
        chrome_options.add_argument("--start-maximized")
        #chrome_options.add_argument('--headless')
        chrome_options.add_extension("extensions/abp.crx")
        
        browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()),options=chrome_options)
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        options.set_preference("media.autoplay.default", 0)  # Allow video auto-play
        options.set_preference("media.volume_scale", "0.0")  # Mute sound
        
        options.set_preference("intl.accept_languages", "en-GB");
        
        browser = webdriver.Firefox(options=options)
#TODOREMOVE        browser.install_addon(path + "/extensions/firefox/ublock_origin.xpi")
    else:
        os.environ.pop(env_key)
        raise ValueError("Unknown browser: {}".format(browser))

    browser.get(url)
    chld = browser.window_handles[0]
    browser.switch_to.window(chld)
    buttons = 0
    while(0 <= buttons < 5):
        try :
            time.sleep(2)    # Remove consent popup
            buttons = browser.find_element(By.LINK_TEXT,'I AGREE')
            buttons.click()
            buttons = -1
        except Exception as e:
            buttons += 1
    return browser


def click_on_next_video(browser, next_video_position=0, first_video=False):
    """
    Click on the required next video and return the link of that video.
    
    :param browser: the selenium browser instance
    :param next_video_position: the next video position on which we should click (default is 0)
    :return: the link of the video on which we clicked
    """
    if first_video:
        elements = browser.find_elements(By.XPATH, "//div[@id='dismissible']")
        titles = []
        videos = []
        for el in elements:
            if len(el.find_elements(By.XPATH, ".//div[contains(@class,'badge-style-type-live-now')]//span[text()='LIVE NOW']"))==0:
                titles.append(el.find_element(By.XPATH, ".//div[@id='details']//a[@id='video-title-link']").text)
                videos.append(el.find_element(By.XPATH, ".//div[@id='details']//a[@id='video-title-link']"))
    else:
        elements = browser.find_elements(By.XPATH, "//div[@id='dismissible' and contains(@class,'video-renderer')]")
        titles = []
        videos = []
        for el in elements:
            if len(el.find_elements(By.XPATH, ".//div[contains(@class,'badge-style-type-live-now')]//span[text()='LIVE NOW']"))==0:
                videos.append(el.find_element(By.XPATH, ".//a[@id='thumbnail'][@href]"))
                titles.append(el.find_element(By.XPATH, ".//span[@id='video-title']").text)
   
    max_cpt = len(videos)
    cpt = next_video_position
    cont = True
    
    
    while cont and cpt<max_cpt:
        if nlp(titles[cpt])._.language['language'] == LANGUAGE_TO_USE:
            cont = False
        else:
            cpt+=1
    
    href = videos[cpt].get_property('href')
    videos[cpt].click()
    time.sleep(1)
    browser.refresh()
    time.sleep(2)
    
    return href

# +
def time_as_sec(time_str):
    time_int = 0
    coef = 1
    for i in time_str.split(':')[::-1]:
        time_int += int(i)*coef
        coef*=60
    return time_int
        
    
def run_experiment():
    """
    Run one experiment with the set parameters
    """
    browser = start_browser()
    cpt=0
    tot=0
    next_video = FIRST_VIDEO_POSITION
    watched_videos = []
    
    try:
        while (cpt<MAX_VIDEOS and not USE_TIME) or (tot<MAX_TOTAL_TIME and USE_TIME):
            time.sleep(2)
            cpt+=1
            watched_videos.append(click_on_next_video(browser, next_video, cpt==1))
            next_video = NEXT_VIDEO_POSITION
            time.sleep(1)
            
            # Ensure that the video is playing
            if len(browser.find_elements(By.XPATH, "//button[@title='Play (k)']"))>0:
                browser.find_element(By.XPATH, "//button[@title='Play (k)']").click()
            
            video_duration = max(time_as_sec(browser.find_element(By.XPATH,"//div[contains(@class,'ytp-bound-time-right')]").get_property('innerHTML'))-VIDEO_TIME_OFFSET, 0)
            time_play = min(WATCH_TIME_VIDEOS, video_duration if video_duration != 0 else WATCH_TIME_VIDEOS)
            tot += time_play
            time.sleep(time_play)
    finally:
        browser.close()
        
    return watched_videos


# -

# Etape 2: Choper les infos des vidéos
def get_description(browser):
    """
    Get the description of the videos currently loaded
    :param browser: The selenium browser instance
    :return: the description of the video
    """
    elems = browser.find_elements(By.XPATH, "//div[@id='description' and contains(@class, 'ytd-video-secondary-info-renderer') ]//*[contains(@class, 'yt-formatted-string')]")
    text = ""
    for el in elems:
        if(el.tag_name == 'span'):
            text += el.get_attribute('innerHTML')
    return text

def get_comments_with_author(browser, nb_comments):
    """
    Get the required number of comments with author information
    :param browser: the selenium browser instance
    :param nb_comments: The number of comments we wish to get
    :return: list of all comments with author information
    """
    all_text = browser.find_elements(By.XPATH,"//ytd-comments[@id='comments']//yt-formatted-string[@id='content-text']")
    authors = browser.find_elements(By.XPATH,"//ytd-comments[@id='comments']//a[@id='author-text']")
    likes = browser.find_elements(By.XPATH, "//ytd-comments[@id='comments']//span[@id='vote-count-middle']")
    result = []
    
    nb_results = min(len(authors), min(len(likes), min(len(all_text), nb_comments)))
    
    for i in range(nb_results):
        result.append((authors[i].get_attribute('href'), authors[i].text,all_text[i].text, str(likes[i].text)))
    return result


def scroll_page(browser, nb_scrolls, delay=0.5):
    """
    Scroll the browser page a given number of time
    :param browser: the selenium browser instance
    :param nb_scrolls: the number of time we should scroll
    :param delay: delay between scroll
    """
    for i in range(1, nb_scrolls):
        browser.execute_script("window.scrollTo(1,5000000000000)")
        time.sleep(delay)

def get_video_information(browser, url):
    """
    Get all the video information currently loaded in the browser
    :param browser: the selenium browser instance
    :param url: the url of the video
    :return: a list of all the information of the videos (url, title, description, channel name, channel link, tags)
    """
    infos=[]
    
    infos.append(url)
    infos.append(browser.find_element(By.XPATH, "//h1[contains(@class,'title') and contains(@class,'ytd-video-primary-info-renderer') ]//yt-formatted-string").text)
    infos.append(get_description(browser))
    infos.append(browser.find_element(By.XPATH, "//div[@id='upload-info']//a").text)
    infos.append(browser.find_element(By.XPATH, "//div[@id='upload-info']//a").get_attribute('href'))
    infos.append(browser.find_element(By.XPATH, "//meta[contains(@name,'keyword')]").get_attribute('content').split(','))
    
    return infos

def format_like_number(text):
    """
    Format the given text to a number
    :param text: the text that should be converted to number
    :return: the number in int
    """
    
    if type(text)==type(0) or text == "":
        return text
    elif 'K' in text:
        return int(float(text[:text.find('K')])*1e3)
    elif 'M' in text:
        return int(float(text[:text.find('M')])*1e6)
    else:
        return int(text)


def load_information(lst):
    all_comments = pd.DataFrame([], columns=['channel_link', 'channel_name', 'text', 'nb_like'])
    all_infos = pd.DataFrame([], columns=['video_link', 'title', 'description', 'channel_link','channel_title', 'keywords'])
    for url in lst:
        browser = start_browser(url)
        scroll_page(browser, int(NB_COMMENTS/10), TIME_BETWEEN_SCROLL)
        comments = get_comments_with_author(browser,NB_COMMENTS)
        df_comments = pd.DataFrame(comments, columns=['channel_link', 'channel_name', 'text', 'nb_like'])
        df_comments['nb_like'] = df_comments['nb_like'].apply(format_like_number)
        all_comments = pd.concat([all_comments,df_comments])
        all_infos = pd.concat([all_infos,pd.DataFrame([get_video_information(browser,url)], columns=['video_link', 'title', 'description', 'channel_link','channel_title', 'keywords'])])
        browser.close()

    all_comments = all_comments.reset_index(drop=True)
    all_infos = all_infos.reset_index(drop=True)
    
    return all_comments, all_infos

def save_dataframes(df_comments, df_infos, compression=COMPRESSION, encoding=ENCODING,path=DATA_PATH):
    """
    Save the dataframes to a disk file
    :param df_comments: the dataframe containing the comments information
    :param df_infos: the dataframe containing the video informations
    :param compression: the compression algorithm that should be used
    :param encoding: the encoding that should be used in the saved files
    :param path: folder in which to save the files
    """
    df_comments.to_csv(path+COMMENTS_DF_PATH, compression=compression,encoding=encoding)
    df_infos.to_csv(path+VIDEOS_DF_PATH,compression=compression,encoding=encoding)

def load_dataframes(compression=COMPRESSION, encoding=ENCODING,path=DATA_PATH):
    """
    Load dataframe from disk
    :param compression: the compression algorithm that should be used
    :param encoding: the encoding that should be used in the saved files
    :param path: folder in which to save the files
    :return: the two dataframes containing comment informations and video informations
    """
    return pd.read_csv(path+COMMENTS_DF_PATH,compression=compression,encoding=encoding), pd.read_csv(path+VIDEOS_DF_PATH,compression=compression,encoding=encoding)
