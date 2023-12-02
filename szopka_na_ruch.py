#%%

import asyncio
import glob
import json
import logging
import random
import serial
import signal
import time
import vlc
import yaml

from kasa import SmartPlug, Discover, SmartDeviceException

import plug_utils

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

CONFIG_FILE = 'config.yaml'

run_loop = True
player = None


#%%

def read_utf8(device):
    global run_loop

    while run_loop:
        line = arduino.readline()
        if line:
            return line.decode('utf-8')
        time.sleep(0.01)


def update_config(conf):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(conf, f)


def sig_int(sig_no, stack_frame):
    global run_loop

    run_loop = False
    logging.debug('Int.')


def run_action(items_to_play, all_items_to_play: list[str], plug_ip):
    logging.debug('Running action...')
    if player.get_state() != vlc.State.Playing:
        if len(items_to_play) < 1:
            items_to_play = random.sample(all_items_to_play, len(all_items_to_play))
            logging.debug(f'Items to play: {items_to_play}')

        next_item = items_to_play.pop()
        logging.info(f'Playing file: {next_item}')
        player.set_mrl(next_item)
        player.play()
        if plug_ip:
            asyncio.run(plug_utils.switch_on(plug_ip))
        logging.info('Lights switched on?')
        #_scheduler.enter(1, 2, check_player_state)
    return items_to_play


@vlc.CallbackDecorators.MediaCloseCb
def media_close_cb(opaque):
    print("CLOSE", opaque)


#%%

if __name__ == '__main__':

    with open(CONFIG_FILE) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    plug_ip = asyncio.run(plug_utils.find_plug(config.get('plug-ip', None)))

    if plug_ip != config.get('plug-ip', None):
        config['plug-ip'] = plug_ip
        update_config(config)


    logging.info('Setting up the mp3 player and files...')
    player = vlc.MediaPlayer()
    i = player.get_instance()
    i.media_new_callbacks(None, None, None, media_close_cb, None)
    mp3_files = glob.glob(config.get('mp3-files', 'sample-mp3') + '/*.mp3')
    logging.info(f'Files to play: {mp3_files}')
    items_to_play = []

    #item = gp.DigitalInputDevice(18, pull_up=True)
    #
    signal.signal(signal.SIGINT, sig_int)
    #signal.signal(signal.SIGUSR1, sig_user)
    #
    #item.when_activated = event_up
    #item.when_deactivated = event_down


    with serial.Serial(port='COM4', baudrate=115200, timeout=.1) as arduino:

        logging.info('Waiting for the motion sensor to calibrate.')
        while True:
            l = read_utf8(arduino)
            if l.startswith('{'):
                    break
            print(l, end='')
            time.sleep(0.1)

        logging.info('Starting the main event loop...')
        while run_loop:
            line = read_utf8(arduino)
            if line:
                j = json.loads(line)
                if j['motion']:
                    items_to_play = run_action(items_to_play, mp3_files, plug_ip)
            time.sleep(0.1)
        
    logging.info('Main loop finished.')
