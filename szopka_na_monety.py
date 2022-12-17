#%%

import gpiozero as gp
import signal
import time
import logging
import sched
import vlc
import glob
import random
import asyncio
import yaml
from kasa import SmartPlug, Discover, SmartDeviceException


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


CONFIG_FILE = 'config.yaml'

COIN_A = 4
COIN_B = 5
COIN_C = 8

run_loop = True
count = 0
a_time = 0.0
_alarm_evt = None
_lights_evt = None
_scheduler = sched.scheduler()


#%%

def update_config(conf):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(conf, f)


async def switch_on(dev_info):
    logging.info('Switching lights on...')
    try:
        p = SmartPlug(dev_info)

        await p.update()
        logging.debug(p.alias)
        await p.turn_on()
    except SmartDeviceException as x:
        logging.error(f'Blad wtyczki: {x}')


async def switch_off(dev_info):
    logging.info('Switching lights off...')
    try:
        p = SmartPlug(dev_info)

        await p.update()
        logging.debug(p.alias)
        await p.turn_off()
    except SmartDeviceException as x:
        logging.error(f'Blad wtyczki: {x}')


async def find_plug(plug_ip=None):
    device = None

    if plug_ip:
        try:
            dev = await Discover.discover_single(plug_ip)
            print(f'Found single device: {dev}')
            if dev.is_plug:
                device = dev.host
            else:
                print(f'Device {dev.host} is not a SmartPlug')
                device = None
        except SmartDeviceException as x:
            print(f'Problems searching for device {plug_ip}: ', x)

    if not device:
        found_devices = await Discover.discover()
        for dev in found_devices:
            print(f'Found device: {dev}...')
            if found_devices[dev].is_plug:
                print(f'Device is a SmartPlug.')
                device = dev
                break
            else:
                print(f'Device is not a SmartPlug. Searching further...')
            
    return device


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
    logging.info('After event down')


def lights_off():
    global _lights_evt
    _lights_evt = None

    logging.info('Lights to off')
    asyncio.run(switch_off(plug_ip))
    logging.info('Lights off')


def coin_check(coin_value=-1):
    global count
    global _alarm_evt
    global _items_to_play

    logging.info('Reseting counters.')
    count = 0
    _alarm_evt = None

    if coin_value == COIN_A or coin_value == COIN_B or coin_value == COIN_C:
        logging.info(f'Coin received: {coin_value}.')
        if len(_items_to_play) < 1:
            _items_to_play = random.sample(range(len(mp3_files)), len(mp3_files))
            logging.debug(f'Items to play: {_items_to_play}')
        logging.info('To pop...')
        next_item = _items_to_play.pop()
        logging.info(f'Playing file: {mp3_files[next_item]}')
        player.set_mrl(mp3_files[next_item])
        player.play()
        asyncio.run(switch_on(plug_ip))
        logging.info('Lights switched on?')
        _scheduler.enter(1, 2, check_player_state)


def check_player_state():
    global _lights_evt

    logging.info(f'Player state {player.get_state()}')
    if player.get_state() == vlc.State.Playing:
        mp3len = (player.get_length() - player.get_time()) / 1000
        logging.info(f'Player is playing, mp3len: {mp3len}')
        if _lights_evt:
            _scheduler.cancel(_lights_evt)
        _lights_evt = _scheduler.enter(mp3len, 3, lights_off)
    else:
        logging.info('Player not playing. Switching lights off...')
        if _lights_evt:
            _scheduler.cancel(_lights_evt)
        lights_off()


def sig_int(sig_no, stack_frame):
    global run_loop

    run_loop = False
    logging.debug('Int.')


class DeviceSurogate(object):
    def __init__(self):
        self.value = 123


def sig_user(sig_no, stack_frame):
    """Simulate coin accepted event on SIG_USR."""
    d = DeviceSurogate()

    for _ in range(5):
        event_up(d)
        event_down(d)
 

#%%

if __name__ == '__main__':

    with open(CONFIG_FILE) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    plug_ip = asyncio.run(find_plug(config.get('plug-ip', None)))

    if plug_ip != config.get('plug-ip', None):
        config['plug-ip'] = plug_ip
        update_config(config)


    logging.info('Setting up the mp3 player and files...')
    player = vlc.MediaPlayer()
    mp3_files = glob.glob(config.get('mp3-files', 'sample-mp3') + '/*.mp3')
    logging.info(f'Files to play: {mp3_files}')
    _items_to_play = []


    item = gp.DigitalInputDevice(18, pull_up=True)

    signal.signal(signal.SIGINT, sig_int)
    signal.signal(signal.SIGUSR1, sig_user)

    item.when_activated = event_up
    item.when_deactivated = event_down

    logging.info('Starting the main event loop...')

    while run_loop:
        _scheduler.run(False)
        time.sleep(0.1)

    item.close()
    logging.info('Done.')
