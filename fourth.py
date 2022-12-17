import vlc
import glob
import random
import logging
import time
from tqdm import tqdm


#%%

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

player = vlc.MediaPlayer()

mp3_files = glob.glob('/home/pi/projects/parafia-szopka/mp3/christmas/*.mp3')
logging.info(f'Files to play: {mp3_files}')

_items_to_play = []

#%%

if len(_items_to_play) < 1:
    _items_to_play = random.sample(range(len(mp3_files)), len(mp3_files))
    logging.debug(f'Items to play: {_items_to_play}')

next_item = _items_to_play.pop()

logging.info(f'Playing file: {mp3_files[next_item]}')
player.set_mrl(mp3_files[next_item])
player.play()

for i in tqdm(range(30)):
    time.sleep(1)