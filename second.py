#%%

import wiringpi
import signal
import time
import statistics
import logging


#%%
run_loop = True
coins = 0
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', filename='second.log')
logging.info('Rozpoczynam wykrywanie monet...')

#%%

def sig_int(sig_no, stack_frame):
    global run_loop

    run_loop = False
    print('Int.')


#%%

wiringpi.wiringPiSetupGpio()

wiringpi.pinMode(18, 0)
wiringpi.digitalWrite(18, 0)
coins = 0

while run_loop:
    value = wiringpi.digitalRead(18)
    #if value > 0:
    if value < 1:
        coins += 1
        logging.debug(f'Value = {value}, coins = {coins}')

    time.sleep(0.01)

# %%
