#%%

import gpiozero as gp
import signal
import time
import logging
import sched
import vlc
import glob
import random


#%%
run_loop = True
count = 0
a_time = 0.0
_alarm_evt = None
_scheduler = sched.scheduler()

COIN_A = 4
COIN_B = 5
COIN_C = 8


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logging.info('Loading mp3 file...')
#p = vlc.MediaPlayer('file:///home/pi/Music/Controlate.mp3')

player = vlc.MediaPlayer()
#mp3_files = glob.glob('/home/pi/Music/*.mp3')
mp3_files = glob.glob('/home/pi/projects/parafia-szopka/sample-mp3/*.mp3')
logging.info(f'Files to play: {mp3_files}')
_items_to_play = []


#%% 

def event_up(device):
    global count
    global a_time
    global _alarm_evt
    
    a_time = time.clock_gettime(time.CLOCK_MONOTONIC)
    logging.info(f'Coin acceptor event up: {count}, value={device.value}')

    if _alarm_evt:
        _scheduler.cancel(_alarm_evt)
        _alarm_evt = None
    count += 1


def event_down(device):
    global _alarm_evt

    d_time = time.clock_gettime(time.CLOCK_MONOTONIC)
    logging.info(f'Coin acceptor event down: {count}, value={device.value}, active_time [ms]: {(d_time-a_time)*1000}')

    if _alarm_evt:
        _scheduler.cancel(_alarm_evt)
    _alarm_evt = _scheduler.enter(0.2, 1, coin_check, argument=[count])


def coin_check(coin_value=-1):
    global count
    global _alarm_evt
    global _items_to_play

    logging.debug('Reseting counters.')
    count = 0
    _alarm_evt = None

    if coin_value == COIN_A or coin_value == COIN_B or coin_value == COIN_C:
        logging.info(f'Coin received: {coin_value}.')
        if len(_items_to_play) < 1:
            _items_to_play = random.sample(range(len(mp3_files)), len(mp3_files))
            logging.debug(f'Items to play: {_items_to_play}')
        next_item = _items_to_play.pop()
        logging.info(f'Playing file: {mp3_files[next_item]}')
        player.set_mrl(mp3_files[next_item])
        player.play()


def sig_int(sig_no, stack_frame):
    global run_loop

    run_loop = False
    logging.debug('Int.')

#%%

item = gp.DigitalInputDevice(18, pull_up=True)

signal.signal(signal.SIGINT, sig_int)

item.when_activated = event_up
item.when_deactivated = event_down


logging.info('Starting the main event loop...')

while run_loop:
    _scheduler.run()
    time.sleep(0.25)

item.close()
print('Done.')

#%%