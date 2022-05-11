from concurrent.futures import process
import os
from os import listdir
from os.path import isfile
import pandas as pd

ENCODING = 'utf-8'
COMPRESSION = 'bz2'

split = '\\' if '\\' in os.getcwd() else '/'
DATA_PATH = f'data{split}'

WATCH_TIME_VIDEOS = 60 * 15#25

VIDEOS_DF_PATH = f"infos.csv.{COMPRESSION}"
THEME_DF_PATH = f"theme.csv.{COMPRESSION}"
CRITERIA = [lambda x: x<5e3, lambda x: x>=5e3 and x<5e4, lambda x: x>=5e4]


def merge_data(compression=COMPRESSION, encoding=ENCODING, path=DATA_PATH):
    """
    Merge all infos files into one info file
    """
    columns = ['walk', 'theme_id', 'theme', 'video_id_in_run', 'video_link', 'title', 'description', 'channel_link', 'channel_title', 'keywords', 'nb_like', 'nb_views', 'nb_sub', 'video_duration', 'watch time']
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
    all_infos.to_csv(f'{path}{split}all_infos.csv.{COMPRESSION}',compression=compression,encoding=encoding)

    return all_infos
        



if __name__ == '__main__':
    merge_data(path=f'{DATA_PATH}P5')