#%%

import asyncio
import datetime as dt
import glob
import json
import logging
import random
import serial
import signal
import sys
import threading
import time
import vlc
import yaml

import plug_utils
import utils
import periods
import motion_reader as mr


logging.getLogger('kasa').setLevel(logging.DEBUG)
logging.getLogger('plug_utils').setLevel(logging.DEBUG)
logger = utils.setup_logger(root_level=logging.DEBUG, file_level=logging.DEBUG, file_name='szopka.log')


CONFIG_FILE = 'config.yaml'

break_event = threading.Event()
switch_lights_off = True
timer = None


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
    break_event.set()
    logger.debug('Int.')


async def run_action(player, items_to_play, all_items_to_play: list[str], plug=None, lights_on_timeout=10, media_runtime_s=60):
    global timer

    logger.debug('Running action...')
    if player.get_state() != vlc.State.Playing and not timer:
        if len(items_to_play) < 1:
            items_to_play = random.sample(all_items_to_play, len(all_items_to_play))
            logger.debug(f'Items to play: {items_to_play}')

        if items_to_play:
            next_item = items_to_play.pop()
            logger.info(f'Playing file: {next_item}')
            player.set_mrl(next_item, f"run-time={media_runtime_s}")
            player.play()
        else:
            timer = threading.Timer(lights_on_timeout, switch_lights_off_func, args=[None])
            timer.start()

        if plug:
            await plug_utils.switch_on(plug)
            logger.debug('Are lights switched on?')

    return items_to_play


def switch_lights_off_func(event, **kwargs):
    global switch_lights_off
    global timer

    logger.debug('Song has finished.')
    switch_lights_off = True
    timer = None


async def main():
    global switch_lights_off
    global timer

    with open(CONFIG_FILE) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)


    night_time = utils.parse_time(config['default-night-time'])
    logger.info(f'Night time starts at: {night_time}')
    day_time = utils.parse_time(config['default-day-time'])
    logger.info(f'Day time starts at {day_time}')

    plug = await plug_utils.find_plug(config.get('plug-ip', None))

    if plug:
        logger.info(f'Found a plug {plug}.')
        if plug.host != config.get('plug-ip', None):
            config['plug-ip'] = plug.host
            update_config(config)

    logger.info('Setting up the mp3 player and files and folders...')
    player = vlc.MediaPlayer()
    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, switch_lights_off_func)

    pds = periods.read_periods(config, data_root=config.get('data-root', '.'))
    cur_period = None
    items_to_play = []

    while not break_event.is_set():

        with serial.Serial(port='COM4', baudrate=115200, timeout=.1) as arduino:
        #with mr.MotionReader('test-data/motion-data.txt', break_event=break_event) as arduino:

            logger.info('Waiting for the motion sensor to calibrate.')
            while not break_event.is_set(): # and (dt.datetime.now().time() >= night_time or dt.datetime.now().time() < day_time):
                l = read_utf8(arduino)
                if l:
                    if l.startswith('{'):
                            break
                    print(l, end='')
                    sys.stdout.flush()
                time.sleep(0.1)

            logger.info('Starting the action loop...')
            while not break_event.is_set() and (dt.datetime.now().time() >= night_time or dt.datetime.now().time() < day_time):
                line = read_utf8(arduino)
                if line:
                    logger.debug(line)
                    try:
                        j = json.loads(line)
                        if j['motion']:
                            tmp_period = periods.find_period(pds, dt.datetime.now(), hint=cur_period)
                            if not tmp_period:
                                logger.info(f'Current date: {dt.datetime.strftime(dt.datetime.now(), "%Y-%m-%d")} is outside of defined periods.')
                                break_event.set()
                                break
                            elif tmp_period != cur_period:
                                cur_period = tmp_period
                                items_to_play = []
                                logger.info(f'Current period: {cur_period.name}, files to play: {cur_period.mp3_files}')

                            items_to_play = await run_action(player, items_to_play, cur_period.mp3_files, plug, config['default-lights-on-timeout'], media_runtime_s=config['media-runtime'])

                    except json.JSONDecodeError as x:
                        logger.warning(f'Error reading json data from the motion sensor: {line}', exc_info=x)

                if switch_lights_off:
                    if plug and player.get_state() != vlc.State.Playing:
                        await plug_utils.switch_off(plug)
                        logger.debug('Are lights switched off?')
                        switch_lights_off = False

                time.sleep(0.1)
        
        if plug:
            await plug_utils.switch_off(plug)
        if timer:
            timer.cancel()
            timer = None

        logger.info(f'The action loop completed. Waiting for night time starting at {night_time}...')
        # A simple hack to allow time.sleep(30) to be interrupted by Ctrl+C on Windows.
        # Unfortunately, much cleaner threading.Event().wait(timeout) cannot be stopped.
        i = 60
        while not break_event.is_set() and i > 0:
            time.sleep(0.5)
            i -= 1

    logger.info('Main loop finished.')


#%%

if __name__ == '__main__':
    signal.signal(signal.SIGINT, sig_int)
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(main())
    except Exception as x:
        logger.error('Error occurred: ', exc_info=x)
        print('\nNaciśnij Enter, aby zakończyć program.')
        input()
    finally:
        logger.info('Done.\n')