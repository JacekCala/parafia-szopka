#%%

import asyncio
import glob
import json
import logging
import platform
import random
import serial
import signal
import sys
import time
import vlc
import yaml

from kasa import SmartPlug, Discover, SmartDeviceException

import plug_utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logging.getLogger('kasa').setLevel(logging.INFO)
logging.getLogger('plug_utils').setLevel(logging.INFO)

CONFIG_FILE = 'config.yaml'

run_loop = True
switch_lights_off = True


#%%

def read_utf8(arduino):

    line = arduino.readline()
    if line:
        return line.decode('utf-8')
    return None


def update_config(conf):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(conf, f)


def sig_int(sig_no, stack_frame):
    global run_loop

    run_loop = False
    logging.debug('Int.')


async def run_action(player, items_to_play, all_items_to_play: list[str], plug=None):

    logging.debug('Running action...')
    if player.get_state() != vlc.State.Playing:
        if len(items_to_play) < 1:
            items_to_play = random.sample(all_items_to_play, len(all_items_to_play))
            logging.debug(f'Items to play: {items_to_play}')

        next_item = items_to_play.pop()
        logging.info(f'Playing file: {next_item}')
        player.set_mrl(next_item)
        player.play()
        if plug:
            await plug_utils.switch_on(plug)
            logging.debug('Are lights switched on?')

    return items_to_play


def vlc_song_finished(event, **kwargs):
    global switch_lights_off

    logging.debug('Song has finished.')
    switch_lights_off = True


async def main():
    global switch_lights_off
    global run_loop

    with open(CONFIG_FILE) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    plug = await plug_utils.find_plug(config.get('plug-ip', None))

    if plug:
        logging.info(f'Found a plug {plug}.')
        if plug.host != config.get('plug-ip', None):
            config['plug-ip'] = plug.host
            update_config(config)

    logging.info('Setting up the mp3 player and files...')
    player = vlc.MediaPlayer()
    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, vlc_song_finished)
    mp3_files = glob.glob(config.get('mp3-files', 'sample-mp3') + '/*.mp3')
    logging.info(f'Files to play: {mp3_files}')
    items_to_play = []

    with serial.Serial(port='COM4', baudrate=115200, timeout=.1) as arduino:

        logging.info('Waiting for the motion sensor to calibrate.')
        while run_loop:
            l = read_utf8(arduino)
            if l:
                if l.startswith('{'):
                        break
                print(l, end='')
                sys.stdout.flush()
            time.sleep(0.1)

        logging.info('Starting the main event loop...')
        while run_loop:
            line = read_utf8(arduino)
            if line:
                try:
                    j = json.loads(line)
                    if j['motion']:
                        items_to_play = await run_action(player, items_to_play, mp3_files, plug)
                except json.JSONDecodeError as x:
                    logging.warning(f'Error reading json data from the motion sensor: {line}', exc_info=x)

            if switch_lights_off:
                if plug and player.get_state() != vlc.State.Playing:
                    await plug_utils.switch_off(plug)
                    logging.debug('Are lights switched off?')
                    switch_lights_off = False

            time.sleep(0.1)
    
    if plug:
        await plug_utils.switch_off(plug)
    logging.info('Main loop finished.')


#%%

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sig_int)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())
    finally:
        logging.info('Done.')