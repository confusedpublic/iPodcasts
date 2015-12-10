#-------------------------------------------------------------------------#
#                                                                         #
#                         scan_for_podcasts.py                            #
#                                                                         #
#-------------------------------------------------------------------------#
#                                                                         #
# This is a fairly simple script which looks in an options file for how   #
# frequently it should scan a directory for new podcast episodes, scans   #
# the directory after that amount of time has passed since the last scan  #
# and then returns the new podcast and xml files in a dictionary.         #
#                                                                         #
#-------------------------------------------------------------------------#

import datetime
import time
import os
import json
import logging

# Check for the configuration file
if not os.path.exists('settings.conf'):
    logging.error("The config file doesn't exist. Please create it!")
    exit()

with open('settings.conf', 'r+') as f:
    settings_data = json.load(f)
settings = settings_data[0]
last_scan = settings_data[1]['last_scan']

# last_scan is the time we last did a scan in the YYYY:MM:DD:HH:MM:SS format
# so now we just need to see if the time now is >= to data[last_scan] + 
# settings[scan_interval]

now = datetime.datetime.now()
last_scan_time = datetime.datetime.strptime(last_scan, "%Y:%m:%d:%H:%M:%S")
difference = (now - last_scan_time).total_seconds()

# Convert the interval into seconds (we now it is in minutes)
interval = int(settings['interval']) * 60

# now check and say whether we should scan!
if difference > interval:
    do_scan = True
else:
    do_scan = False