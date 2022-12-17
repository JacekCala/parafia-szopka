# %%

import asyncio
import yaml
from kasa import SmartPlug, Discover, SmartDeviceException

CONFIG_FILE = 'config.yaml'

# %%

with open(CONFIG_FILE) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def update_config(conf):
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(conf, f)


async def main(dev_info):

    p = SmartPlug(dev_info)

    await p.update()
    print(p.alias)
    #print(p.emeter_realtime)
    await p.turn_off()


# %%

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

# %%

plug_ip = asyncio.run(find_plug(config.get('plug-ip', None)))

if plug_ip != config.get('plug-ip', None):
    config['plug-ip'] = plug_ip
    update_config(config)

asyncio.run(main(plug_ip))