#%%

import datetime as dt
import yaml

import periods

#%%

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

#%%
    
p = periods.read_periods(config, 'sample-mp3')
p
# %%

periods.find_period(p, dt.datetime.now()-dt.timedelta(40))
# %%
