#%%

import logging

from kasa import SmartPlug, Discover, SmartDeviceException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create a console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create a formatter
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
# add the formatter to the handler
ch.setFormatter(formatter)
# add the console handler to the logger
logger.addHandler(ch)


async def find_plug(plug_ip=None):
    device = None

    if plug_ip:
        try:
            dev = await Discover.discover_single(plug_ip)
            logger.info(f'Found single device: {dev}')
            if dev.is_plug:
                device = dev.host
            else:
                logger.info(f'Device {dev.host} is not a SmartPlug')
                device = None
        except SmartDeviceException as x:
            logger.warning(f'Problems searching for device {plug_ip}: ', x)

    if not device:
        found_devices = await Discover.discover()
        for dev in found_devices:
            logger.info(f'Found device: {dev}...')
            if found_devices[dev].is_plug:
                logger.info(f'Device is a SmartPlug.')
                device = dev
                break
            else:
                logger.info(f'Device is not a SmartPlug. Searching further...')
            
    return device


async def switch_on(dev_info):
    logger.info('Switching lights on...')
    try:
        p = SmartPlug(dev_info)

        await p.update()
        logger.debug(p.alias)
        await p.turn_on()
    except SmartDeviceException as x:
        logger.error(f'SmartPlug error: {x}')


async def switch_off(dev_info):
    logger.info('Switching lights off...')
    try:
        p = SmartPlug(dev_info)

        await p.update()
        logger.debug(p.alias)
        await p.turn_off()
    except SmartDeviceException as x:
        logger.error(f'SmartPlug error: {x}')
