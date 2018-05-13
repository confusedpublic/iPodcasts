# -*- coding: utf-8 -*-
#!/usr/bin/env python


import datetime
import json
import os
import logging
import logging.handlers
import threading

import ipodcasts.scheduler as SCHEDULER
from ipodcasts.podcast_subscription_managers import PodcastSubscriptionManager
from ipodcasts.find_new_podcasts import PodcastDirectoryWalker


# Need to set directory of settings.conf to be an absolute path
# Caused no ends of problems when trying to run as daemon
CONFIG_FILE = "/ipodcasts.service/settings.conf"

# Get the log directory from the settings file:
with open(CONFIG_FILE, 'r+') as f:
    json_data = json.load(f)
settings = json_data[0]

# Set up logging
log_file = settings['log_file']
log_level = logging.getLevelName(settings['log_level'])
log_format = logging.Formatter('%(name)s: %(levelname)s %(asctime)s: %(message)s')
# Rotate the logs every week, keep 4 weeks of logs (as they shouldn't be too big)
log_handler = logging.handlers.TimedRotatingFileHandler(log_file, when="D", interval=7, backupCount=4)
log_handler.setFormatter(log_format)
logger = logging.getLogger("iPodcasts")
logger.addHandler(log_handler)
logger.setLevel(log_level)

# Just a quick check before going any further that the podcast directory has been set
if not settings['podcast_dir']:
    logger.error("No podcast directory given. Please set this in the config file.")
    exit()

# Now check whether the podcast directory actually exists!
if not os.path.isdir(settings['podcast_dir']):
    logger.error("The podcast directory set in the config file does not exist. Please set this to an existing directory.")

podcast_dir = json_data[0]['podcast_dir']
podcast_feed_dir = json_data[0]['podcast_feed_dir']
webpage_path = json_data[0]['webpage_path']

# Set the scan interval, convert from minutes to a timedelta:
scan_interval = datetime.timedelta(minutes=settings['interval'])


class iPodcasts(object):
    """ This class runs the scheduled scan for the podcasts. It is what is
        initialised by the Scheduler class at the time period set in the settings
        file.
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False
        
    def run(self, force=False):
        if self.amActive:
            return
        
        self.amActive = True
        _ = force
    
        logger.info("Initialising iPodcast scan")

        podcast_walker = PodcastDirectoryWalker(podcast_dir)
        podcasts = podcast_walker.get_podcasts()

        if podcasts:
            podcast_manager = PodcastSubscriptionManager(podcasts, podcast_feed_dir, webpage_path)
            podcast_manager.add_new_episodes()
            logger.info("Scan complete")
        else:
            logger.info("No new podcasts found")
        
        self.amActive = False


# Construct the podcast scheduler
PodcastScheduler = SCHEDULER.Scheduler(iPodcasts(), cycleTime=scan_interval, threadName="PodcastScheduler")

# Run the podcast scheduler
PodcastScheduler.run()
