import logging

from kasa import SmartPlug, Discover, SmartDeviceException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def find_plug(plug_ip=None):
    device = None

    if plug_ip:
        try:
            dev = await Discover.discover_single(plug_ip)
            logger.info(f'Found single device: {dev}')
            if dev.is_plug:
                device = dev
            else:
                logger.info(f'Device {dev.host} is not a SmartPlug')
                device = None
        except SmartDeviceException as x:
            logger.warning(f'Problems searching for device {plug_ip}: ', exc_info=x)

    if not device:
        found_devices = await Discover.discover()
        for dev_name, dev in found_devices.items():
            logger.info(f'Found device: {dev}...')
            if dev.is_plug:
                logger.info(f'Device {dev_name} is a SmartPlug.')
                device = dev
                break
            else:
                logger.info(f'Device is not a SmartPlug. Searching further...')
            
    return device


async def switch_on(device):
    logger.info('Switching lights on...')
    try:
        await device.update()
        logger.debug(device.alias)
        await device.turn_on()
    except SmartDeviceException as x:
        logger.error('SmartPlug error: ', exc_info=x)


async def switch_off(device):
    logger.info('Switching lights off...')
    try:
        await device.update()
        logger.debug(device.alias)
        await device.turn_off()
    except SmartDeviceException as x:
        logger.error('SmartPlug error: ', exc_info=x)
