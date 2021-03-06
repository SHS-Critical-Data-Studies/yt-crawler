import os
from os import listdir, makedirs
from os.path import isfile, isdir, join
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import pandas as pd
from selenium import webdriver
import spacy
from spacy_langdetect import LanguageDetector
from spacy.language import Language
import numpy as np
import en_core_web_sm
nlp = en_core_web_sm.load()


@Language.factory('language_detector')
def language_detector(nlp, name):
    return LanguageDetector()

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe('language_detector', last=True)

MAX_VIDEO_POSITION = 8
WATCH_TIME_VIDEOS = 60 * 15#25
MAX_TOTAL_TIME = 60 * 60 * 4#10
MAX_VIDEOS = 30
USE_TIME = True
TIME_BETWEEN_SCROLL = 0.5
NB_COMMENTS = 100
LANGUAGE_TO_USE = 'en'
VIDEO_TIME_OFFSET = 30
CRITERIA = [lambda x: x<5e3, lambda x: x>=5e3 and x<5e4, lambda x: x>=5e4]

ENCODING = 'utf-8'
COMPRESSION = 'bz2'

split = '\\' if '\\' in os.getcwd() else '/'
DATA_PATH = f'data{split}'
COMMENTS_DF_PATH = f"comments.csv.{COMPRESSION}"
VIDEOS_DF_PATH = f"infos.csv.{COMPRESSION}"
HOME_VIDEOS_DF_PATH = f"first.csv.{COMPRESSION}"
THEME_DF_PATH = f"theme.csv.{COMPRESSION}"
ALL_INFOS_DF_PATH = f"all_infos.csv.{COMPRESSION}"


def start_browser(url="https://www.youtube.com", browser=None, agree=True):
    """
    Start and return the browser loaded at a given url
    Parameters:
    -----------
        - url: start the browser on this url
        - browser: browser name to start
        - agree: if true, accept the popup on youtube
    Returns:
    -----------
        - browser: the selenium browser instance
    """
    env_key = "YTCRAWLER_BROWSER"
    path = os.getcwd()
    
    if(browser == None):
        browser = os.environ.get(env_key)
    if(browser == None):
        print("No browser defined: ")
        browser = input()
    browser = os.environ[env_key] = browser

    if browser == "chrome":
        from webdriver_manager.chrome import ChromeDriverManager   
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--lang=en")
        chrome_options.add_argument("--start-maximized")
        #chrome_options.add_argument('--headless')
        chrome_options.add_extension(f'{path}{split}extensions{split}abp.crx')
        
        browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()),options=chrome_options)
        #browser = webdriver.Chrome(executable_path="C:\Program Files\Google\Chrome\Application\chrome.exe", options=chrome_options)
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        options.set_preference("media.autoplay.default", 0)  # Allow video auto-play
        options.set_preference("media.volume_scale", "0.0")  # Mute sound
        options.set_preference("intl.accept_languages", "en-GB");
        
        browser = webdriver.Firefox(options=options)
        browser.install_addon(f'{path}{split}extensions{split}firefox{split}ublock_origin.xpi')
    else:
        os.environ.pop(env_key)
        raise ValueError(f"Unknown browser: {browser}")
    
    #browser.implicitly_wait(10)
    browser.get(url)
    chld = browser.window_handles[0]
    browser.switch_to.window(chld)
    buttons = 0
    if(agree):
        while(0 <= buttons < 5):
            try :
                time.sleep(2)    # Remove consent popup
                button = browser.find_element(By.LINK_TEXT,'I AGREE')
                button.click()
                time.sleep(2)
                buttons = -1
            except Exception as e:
                button = browser.find_elements(By.XPATH,'.//ytd-button-renderer//yt-formatted-string')
                for btn in button:
                    if('ACCEPT ALL' in btn.text):
                        btn.click()
                        buttons = -2
                        break
                time.sleep(2)
                buttons += 1
    return browser

def get_next_video_id(max_accepted_value, excluded_nb, mean_poisson = 2.5):
    """
    Get next video id in range [0, `max_accepted_value`) \ excluded_nb
    Parameters:
    -----------
        - max_accepted_value: maximum number of id
        - excluded_nb: list of excluded id
        - mean_poisson: mean of poisson distribution
    Returns:
    -----------
        - id: random id
    """
    cur = -1
    while( cur < 0 or cur >= max_accepted_value or cur in excluded_nb):
        cur = int(np.random.poisson(mean_poisson))
    return cur 

def click_on_next_video(browser, first_video=False):
    """
    Click on the required next video and return the link of that video.
    Parameters:
    -----------
        - browser: the selenium browser instance
        - first_video: True if, and only if, the next video is on homepage
    Returns:
    -----------
        - href: the link of the video on which we clicked
        - url: list of URL that coud be selected
    """
    titles = []
    videos = []
    url = []
    if first_video:
        elements = browser.find_elements(By.XPATH, "//div[@id='dismissible']")
        for el in elements:
            if len(el.find_elements(By.XPATH, ".//div[contains(@class,'badge-style-type-live-now')]//span[text()='LIVE NOW']"))==0:
                e = el.find_element(By.XPATH, ".//div[@id='details']//a[@id='video-title-link']")
                videos.append(e)
                titles.append(e.text)
                url.append(e.get_property('href'))
    else:
        elements = browser.find_elements(By.XPATH, "//div[@id='dismissible' and contains(@class,'video-renderer')]")
        for el in elements:
            if len(el.find_elements(By.XPATH, ".//div[contains(@class,'badge-style-type-live-now')]//span[text()='LIVE NOW']"))==0:
                videos.append(el.find_element(By.XPATH, ".//a[@id='thumbnail'][@href]"))
                titles.append(el.find_element(By.XPATH, ".//span[@id='video-title']").text)
   
    max_cpt = len(videos)
    cont = True
    
    cpt = 0
    
    excl = []
    while cont and len(excl)<max_cpt:
        cpt = int(get_next_video_id(max_cpt, excl))
        if cpt < 0 or cpt >= len(videos):
            excl.append(cpt)
        else:
            if nlp(titles[cpt])._.language['language'] == LANGUAGE_TO_USE:
                cont = False
            else:
                excl.append(cpt)
    
    href = videos[cpt].get_property('href')
    browser.get(href)
    time.sleep(2)
    
    return href, url

def get_starting_videos_diff_magnitude(keywords, criteria=CRITERIA, browser_name=None):
    """
    Return a dictionnary of videos satisfying the given criteria
    Parameters:
    -----------
        - criteria: the list of criterion we want to satisfy
        - keywords: the list of keywords to search in order to get the videos
        - browser_name: browser name to start
    Returns:
    -----------
        - a dictionnary of videos satisfying the given criteria (criterion index -> url of the videos)
    """
    
    br = start_browser("https://www.youtube.com/results?search_query="+"+".join(keywords).replace(' ', '+'), browser_name)
    time.sleep(10)
    DIV = "//div[@id='dismissible' and contains(@class,'ytd-video-renderer')]"
    all_videos = br.find_elements(By.XPATH, DIV)
    
    full = False
    cpt = 0
    # Dictionnary to store the results
    result = {}
    start_scrolls = 0
    nb_live = 0
    while not full and cpt < 1000:
        while(cpt >= len(all_videos)):
            scroll_page(br, 10, delay=1, from_scrolls=(start_scrolls)*10 + 1)
            all_videos = br.find_elements(By.XPATH, DIV)
            start_scrolls += 1
            time.sleep(1)
            
        if("badge-style-type-live-now" in str(all_videos[cpt].get_attribute('innerHTML'))) :
            nb_live += 1
        else :
            # get the number of views as int
            views = br.find_elements(By.XPATH, f"{DIV}//span[contains(@class,'ytd-video-meta-block') and contains(text(),'views')]")[cpt - nb_live].text
            views = views[0: len(views)-len(" views")]
            views = format_like_number(views)

            if(views !='None'):
                for i, cr in enumerate(criteria):
                    # Check if the video satisfies any of the remaining criteria
                    if i not in result and (cr(views)):
                        # Get relevant attributes 
                        title = br.find_elements(By.XPATH, f"{DIV}//h3[contains(@class,'title-and-badge')]")[cpt].text
                        desc = br.find_elements(By.XPATH,f"{DIV}//yt-formatted-string[contains(@class, 'style-scope') and contains(@class, 'ytd-video-renderer')  and contains(@class, 'metadata-snippet-text') and not(contains(@class, 'metadata-snippet-text-navigation')) ]")[cpt].text

                        # Since the video satisfies the current criterion
                        # check that it is an english video by checking the title and the description with spacy
                        if(nlp(title)._.language['language'] == LANGUAGE_TO_USE and nlp(desc)._.language['language'] == LANGUAGE_TO_USE):
                            # If both detected languages are indeed, the video satisfies the current criterion
                            result[i] = br.find_elements(By.XPATH, f"{DIV}//a[@id='thumbnail'][@href]")[cpt].get_property('href')
                            # as we use mutually exclusive criteria, we cannot satisfy another criterion therefore we can safely break the inner loop
                            break
        # Check ending conditions, i.e. if we have aas many criteria as results (i.e. if we find one video for each criterion)
        full = (len(result) == len(criteria))
        # Increment the counter to go to the next vidoe
        cpt +=1
    br.close()
    return [result[i] for i in range(len(criteria))]

def get_theme(browser_name=None, nb=8):
    """
    Get themes from news.google.com
    Parameters:
    -----------
        - browser_name: browser name to start
        - nb: number of themes
    Returns:
    -----------
        - themes: list of themes
    """
    browser = start_browser(url='https://news.google.com/topstories?hl=en&gl=CH', browser=browser_name, agree=False)
    time.sleep(1)
    buttons = browser.find_elements(By.XPATH  ,'//span')
    for btn in buttons:
        if('I agree' in btn.text):
            btn.click()
            break
    time.sleep(1)
    world = browser.find_element(By.XPATH, '//div[@aria-label="World"]/a').get_attribute('href')
    browser.get(world)
    time.sleep(1)
    scroll_page(browser, 10, delay=1)
    time.sleep(1)
    titles = browser.find_elements(By.XPATH, '//c-wiz//c-wiz/div/div/div/main/c-wiz/div/div/main/div/div//h3/a')
    
    text = []
    for title in titles:
        ents = nlp(title.text).ents
        if (not any(any(str(s).lower() in [str(i).lower() for i in l] for s in ents) for l in text)):
            text.append(ents)
            if (nb >= 0 and len(text)>=nb):
                break
    browser.close()
    return [[str(i) for i in l] for l in text]

def time_as_sec(time_str):
    """
    Convert string time to int
    Parameters:
    -----------
        - time_str: the time string to convert
    Returns:
    -----------
        - time: result of conversion
    """
    time_int = 0
    coef = 1
    for i in time_str.split(':')[::-1]:
        time_int += int(i)*coef
        coef*=60
    return time_int

def run_experiment(filename, browser_name=None, version=None, theme=None, url=None):
    """
    Run one experiment with the set parameters
    Parameters:
    -----------
        - filename: The name of the experiment
        - browser_name: The name of the browser
        - version: The version of the experiment
        - theme: The theme to use for run
        - url: The URL to start the experiment
    Returns:
    -----------
        - watched_videos: list of videos watched on the experiment
        - all_comments: list of all comments on the experiment
        - all_infos: all info about the experiment
        - home_video: list of videos on homepage
        - themes: selected theme or `None`
    """
    browser = start_browser(browser=browser_name)
    cpt=0
    tot=0
    watched_videos = []
    home_video = []
    themes = pd.DataFrame([])
    
    all_comments = pd.DataFrame([], columns=['video_link', 'channel_link', 'channel_name', 'text', 'nb_like'])
    all_infos = pd.DataFrame([], columns=['video_link', 'title', 'description', 'channel_title', 'channel_link', 'keywords', 'nb_like', 'nb_views', 'nb_sub', 'video_duration', 'watch time'])
    try:
        while (cpt<MAX_VIDEOS and not USE_TIME) or (tot<MAX_TOTAL_TIME and USE_TIME):
            time.sleep(2)
            
            if(theme != None and cpt==0):
                tmp = get_starting_videos_diff_magnitude(
                    theme,
                    [lambda x:(x<1e5 if(url == None) else True)for i in range(16)],
                    browser_name=browser_name)
                if(url == None):
                    url = tmp[0]
                browser.get(url)
                themes = pd.DataFrame(theme)
                time.sleep(2)
            elif(url != None and cpt==0):
                tmp = []
                browser.get(url)
                time.sleep(2)
            else:
                url, tmp = click_on_next_video(browser, first_video=(cpt==0))
            
            if(cpt==0):
                home_video = pd.DataFrame(tmp)
            cpt+=1
            watched_videos.append(url)
            time.sleep(1)
            
            start_time = time.time()
            
            # Ensure that the video is playing
            if len(browser.find_elements(By.XPATH, "//button[@title='Play (k)']"))>0:
                browser.find_element(By.XPATH, "//button[@title='Play (k)']").click()
            
            video_duration = max(time_as_sec(browser.find_element(By.XPATH,"//div[contains(@class,'ytp-bound-time-right')]").get_property('innerHTML')), 0)
            vd = max(video_duration-VIDEO_TIME_OFFSET, 0)
            time_play = min(WATCH_TIME_VIDEOS, vd if vd != 0 else WATCH_TIME_VIDEOS)
            
            tot += time_play
            df_comments, df_infos = load_information(url, browser_name=browser_name, video_duration=video_duration, time_play=time_play)
            all_comments = pd.concat([all_comments, df_comments])
            all_infos = pd.concat([all_infos, df_infos])
            
            # Save the links retrieved during random walk
            save_dataframes(all_comments, all_infos, home_video, themes,
                            path=(f'data/{version}/{filename}' if(version!=None) else f'data/{filename}'))
            
            while (time.time() - start_time < time_play):
                time.sleep(max(1, time_play - (time.time() - start_time)))
    finally:
        browser.close()
    return watched_videos, all_comments, all_infos, home_video, themes

# Etape 2: Choper les infos des vid??os
def get_description(browser):
    """
    Get the description of the videos currently loaded
    Parameters:
    -----------
        - browser: the selenium browser instance
    Returns:
    -----------
        - text: description of the videos
    """
    text = ""
    elems = browser.find_elements(By.XPATH, "//div[@id='description' and contains(@class, 'ytd-video-secondary-info-renderer') ]//*[contains(@class, 'yt-formatted-string')]")
    if(len(elems) > 0):
        for el in elems:
            if(el.tag_name == 'span'):
                text += el.get_attribute('innerHTML')
    else:
        elems = browser.find_element(By.XPATH, "//yt-formatted-string[@class='content style-scope ytd-video-secondary-info-renderer']")
        text = elems.text
    return text

def get_comments_with_author(browser, nb_comments):
    """
    Get the required number of comments with author information
    Parameters:
    -----------
        - browser: the selenium browser instance
        - nb_comments: the number of comments to get
    Returns:
    -----------
        - comments: list of all comments with author information
    """
    all_text = browser.find_elements(By.XPATH,"//ytd-comments[@id='comments']//yt-formatted-string[@id='content-text']")
    authors = browser.find_elements(By.XPATH,"//ytd-comments[@id='comments']//a[@id='author-text']")
    likes = browser.find_elements(By.XPATH, "//ytd-comments[@id='comments']//span[@id='vote-count-middle']")
    result = []
    
    nb_results = min(len(authors), min(len(likes), min(len(all_text), nb_comments)))
    
    for i in range(nb_results):
        # Check language
        result.append((authors[i].get_attribute('href'), authors[i].text,all_text[i].text, str(likes[i].text)))
    return result


def scroll_page(browser, nb_scrolls, delay=3, from_scrolls = 1):
    """
    Scroll the browser page a given number of time
    Parameters:
    -----------
        - browser: the selenium browser instance
        - nb_scrolls: the number of scroll
        - delay: the number of seconds to wait before next scroll
        - from_scrolls: the number of scroll already done before
    """
    for i in range(int(from_scrolls), int(nb_scrolls)):
        browser.execute_script("const height = window.innerHeight||document.documentElement.clientHeight||document.body.clientHeight;"+
                 f"window.scrollTo(1,{i} * height);")
        time.sleep(delay)

def get_video_information(browser, url, video_duration=None, time_play=None):
    """
    Get all the video information currently loaded in the browser
    Parameters:
    -----------
        - browser: the selenium browser instance
        - url: the url of the video
        - video_duration: the duration of the video
        - time_play: the watched time of the video
    Returns:
    -----------
        - infos: a list of all the information of the videos
    """
    infos=[]
    
    infos.append(url)
    try :
        infos.append(browser.find_element(By.XPATH, "//h1[contains(@class,'title') and contains(@class,'ytd-video-primary-info-renderer') ]//yt-formatted-string").text)
    except Exception as e:
        infos.append('None')
    try :
        infos.append(get_description(browser))
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//div[@id='upload-info']//a").text)
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//div[@id='upload-info']//a").get_attribute('href'))
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//meta[contains(@name,'keyword')]").get_attribute('content').split(','))
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//div[@id='top-level-buttons-computed']//a//yt-formatted-string[@aria-label]").get_attribute('aria-label').split()[0])
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//div[@class='style-scope ytd-video-primary-info-renderer']//span[@class='view-count style-scope ytd-video-view-count-renderer']").text.split()[0])
    except Exception as e:
        infos.append('None')
    try :
        infos.append(browser.find_element(By.XPATH, "//yt-formatted-string[@id='owner-sub-count']").text.split()[0])
    except Exception as e:
        infos.append('None')
    infos.append(video_duration)
    infos.append(time_play)
    
    return infos

def format_like_number(text):
    """
    Format the given text to a number
    Parameters:
    -----------
        - text: the text that should be converted to number
    Returns:
    -----------
        - likes: the number in int or `None`
    """
    try:
        if type(text)==type(0) or text == "":
            return text
        elif 'K' in text:
            return int(float(text[:text.find('K')])*1e3)
        elif 'M' in text:
            return int(float(text[:text.find('M')])*1e6)
        else:
            return int(text)
    except:
        return 'None'


def load_information(url, browser_name=None, video_duration=None, time_play=None):
    """
    Load information of a video
    Parameters:
    -----------
        - url: The URL of the video
        - browser_name: The name of the browser
        - video_duration: The duration of the video
        - time_play: The watched time of the video
    Returns:
    -----------
        - all_comments: A list of all comments
        - all_infos: A list of all information about the video
    """
    columns = ['video_link', 'title', 'description', 'channel_title', 'channel_link', 'keywords', 'nb_like', 'nb_views', 'nb_sub', 'video_duration', 'watch_time']
    all_comments = pd.DataFrame([], columns=['video_link', 'channel_link', 'channel_name', 'text', 'nb_like'])
    all_infos = pd.DataFrame([], columns=columns)
    
    browser = start_browser(url=url, browser=browser_name)
    scroll_page(browser, NB_COMMENTS, TIME_BETWEEN_SCROLL)
    comments = get_comments_with_author(browser,NB_COMMENTS)
    df_comments = pd.DataFrame(comments, columns=['channel_link', 'channel_name', 'text', 'nb_like'])
    df_comments['video_link'] = url
    df_comments['nb_like'] = df_comments['nb_like'].apply(format_like_number)
    all_comments = df_comments
    all_infos = pd.DataFrame([get_video_information(browser, url, video_duration=video_duration, time_play=time_play)], columns=columns)
    browser.close()

    all_comments = all_comments.reset_index(drop=True)
    all_infos = all_infos.reset_index(drop=True)
    
    return all_comments, all_infos

check = lambda x : x == 'None' or pd.isna(x)

def get(df, b):
    if(sum(df.apply(check)) > 0):
        url = df['video_link']
        print(url)
        b.get(url)
        time.sleep(2)

        txt = b.find_element(By.XPATH,"//div[contains(@class,'ytp-bound-time-right')]").get_property('innerHTML')
        video_duration = max(time_as_sec(txt), 0)
        vd = max(video_duration-VIDEO_TIME_OFFSET, 0)
        time_play = min(WATCH_TIME_VIDEOS, vd if vd != 0 else WATCH_TIME_VIDEOS)

        ls = get_video_information(b, url, video_duration=video_duration, time_play=time_play)
        
        def add(txt, id_):
            if(check(df[txt])):
                df[txt] = ls[id_]
                
        add('title', 1)
        add('description', 2)
        add('channel_title', 3)
        add('channel_link', 4)
        add('keywords', 5)
        add('nb_like', 6)
        add('nb_views', 7)
        add('nb_sub', 8)
        add('video_duration', 9)
        add('watch time', 10)
    
    return df
    
def reload_data(path = 'data'):
    encoding = 'utf-8'
    compression = 'bz2'

    if(not isdir(join(path, 'tmp'))):
        makedirs(join(path, 'tmp'))

    files = [f for f in listdir(path) if 'infos'in f and isfile(join(path, f))]
    b = start_browser(browser='firefox')
    for f in files:
        if(not isfile(join(path, 'tmp', f))):
            print(f)
            df = pd.read_csv(join(path, f), compression=compression,encoding=encoding, index_col=0)
            tmp = df.apply(lambda r : get(r, b), axis=1)
            tmp.to_csv(join(path, 'tmp', f),compression=compression,encoding=encoding)
        else :
            df = pd.read_csv(join(path, f), compression=compression,encoding=encoding, index_col=0)
            df_tmp = pd.read_csv(join(path, 'tmp', f), compression=compression,encoding=encoding, index_col=0)
            print(f, len(df), len(df_tmp))
    b.close()

def merge_data(compression=COMPRESSION, encoding=ENCODING, path=DATA_PATH):
    """
    Merge all infos files into one info file
    """
    columns = ['walk', 'theme_id', 'theme', 'video_id_in_run', 'video_link', 'title', 'description', 'channel_title', 'channel_link', 'keywords', 'nb_like', 'nb_views', 'nb_sub', 'video_duration', 'watch_time']
    print(path)
    all_infos = pd.DataFrame([], columns=columns)
    
    theme_ids = {}
    last_theme_id = {}

    for filename in [filename for filename in listdir(path) if (filename.endswith(VIDEOS_DF_PATH) and isfile(f'{path}{split}{filename}'))]:
        filename = filename[0:-(len(VIDEOS_DF_PATH) + 1)]

        process_id = int(filename.split('.')[-1])

        df_infos = pd.read_csv(f'{path}{split}{filename}.{VIDEOS_DF_PATH}', compression=compression, encoding=encoding, index_col=0)
        df_theme = pd.read_csv(f'{path}{split}{filename}.{THEME_DF_PATH}', compression=compression, encoding=encoding, index_col=0)

        theme_text = []
        df_theme['0'].apply(lambda x:theme_text.extend(x.split(' ')))
        theme_text = list(set(theme_text))
        theme_text.sort()
        theme_text = ' '.join(theme_text)

        if(process_id in last_theme_id and last_theme_id[process_id].split(':')[1] == theme_text):
            pass
        else:
            idx = 0
            if(theme_text in theme_ids):
                idx = theme_ids[theme_text] + 1
            theme_ids[theme_text] = idx
            last_theme_id[process_id] = f'{idx}:{theme_text}'
        
        df_infos['walk'] = filename
        df_infos['theme_id'] = last_theme_id[process_id]
        df_infos['theme'] = theme_text

        df_infos['watch time'] = df_infos['watch time'].apply(lambda x:min(int(x), WATCH_TIME_VIDEOS))

        all_infos = pd.concat([all_infos, df_infos])

    all_infos['video_id_in_run'] = df_infos.groupby(['walk']).cumcount()
    all_infos.to_csv(f'{path}{split}{ALL_INFOS_DF_PATH}',compression=compression,encoding=encoding)

    return all_infos

def save_dataframes(df_comments, df_infos, df_home_video, df_themes, compression=COMPRESSION, encoding=ENCODING, path=DATA_PATH):
    """
    Save the dataframes to a disk file
    :param df_comments: the dataframe containing the comments information
    :param df_infos: the dataframe containing the video informations
    :param df_home_video: the dataframe containing the url of videos on home page
    :param compression: the compression algorithm that should be used
    :param encoding: the encoding that should be used in the saved files
    :param path: folder in which to save the files
    """
    path = path.replace('/', split)
    df_comments.to_csv(f'{path}.{COMMENTS_DF_PATH}', compression=compression, encoding=encoding)
    df_infos.to_csv(f'{path}.{VIDEOS_DF_PATH}', compression=compression, encoding=encoding)
    df_home_video.to_csv(f'{path}.{HOME_VIDEOS_DF_PATH}', compression=compression, encoding=encoding)
    df_themes.to_csv(f'{path}.{THEME_DF_PATH}', compression=compression, encoding=encoding)

def load_dataframes(compression=COMPRESSION, encoding=ENCODING, path=DATA_PATH):
    """
    Load dataframe from disk
    :param compression: the compression algorithm that should be used
    :param encoding: the encoding that should be used in the saved files
    :param path: folder in which to save the files
    :return: the two dataframes containing comment informations and video informations
    """
    return \
        pd.read_csv(f'{path}.{COMMENTS_DF_PATH}', compression=compression, encoding=encoding, index_col=0),\
        pd.read_csv(f'{path}.{VIDEOS_DF_PATH}', compression=compression, encoding=encoding, index_col=0),\
        pd.read_csv(f'{path}.{HOME_VIDEOS_DF_PATH}', compression=compression, encoding=encoding, index_col=0),\
        pd.read_csv(f'{path}.{THEME_DF_PATH}', compression=compression, encoding=encoding, index_col=0)
