#!/usr/bin/env python

# For date related activities
import datetime
import time
# For parsing and altering the settings file
import json
# For file & directory operations
import os
# For logging
import logging
# For scheduling the scan
import threading
# Import scheduler.py to run the scheduling of the scan
import scheduler as SCHEDULER
# import generate_podcast_list to do all the fancy auto-generating
import generate_podcast_list as GENERATE
# Import the new XML files
import scan_for_xml as XMLs

##############
##############
# IMPORTANT
# TO DO
#
# Need to set directory of settings.conf to be an absolute path
# Caused no ends of problems when trying to run as daemon
CONFIG_FILE = "/ipodcasts/settings.conf"

# Get the log directory from the settings file:
with open(CONFIG_FILE, 'r+') as f:
    json_data = json.load(f)
settings = json_data[0]

# Set up logging
log_file = settings['log_file']
log_level = logging.getLevelName(settings['log_level'])
logging.basicConfig(filename=log_file, format="%(levelname)s: %(asctime)s: %(message)s", level=log_level)

# Just a quick check before going any further that the podcast directory has been set
if not settings['podcast_dir']:
    logging.error("No podcast directory given. Please set this in the config file.")
    exit()

# Now check whether the podcast directory actually exists!
if not os.path.isdir(settings['podcast_dir']):
    logging.error("The podcast directory set in the config file does not exist. Please set this to an existing directory.")

# Make sure the podcast directory is clean; add a / if needed:
if json_data[0]['podcast_dir'].endswith("/"):
    podcast_dir = json_data[0]['podcast_dir']
else:
    podcast_dir = json_data[0]['podcast_dir'] + "/"
  
# Make sure the podcast feed directory is clean; add a / if needed:
if json_data[0]['podcast_feed_dir'].endswith("/"):
    podcast_feed_dir = json_data[0]['podcast_feed_dir']
else:
    podcast_feed_dir = json_data[0]['podcast_feed_dir'] + "/"

# Set the scan interval, convert from minutes to a timedelta:
scan_interval = datetime.timedelta(minutes=settings['interval'])

class iPodcasts():
#-------------------------------------------------------------------------#
# This class runs the scheduled scan for the podcasts. It is what is
# initialised by the Scheduler class at the time period set in the settings
# file.

    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False
        
    def run(self, force=False):
        if self.amActive:
            return
        
        self.amActive = True
        _ = force
    
        logging.info("Initialising iPodcast scan")

        # Generate the list of new podcasts & their XML files
        XMLs.podcast_walk(podcast_dir)
        
        # Push the new podcast list to the log if it contains anything...
        if XMLs.new_podcasts:
            logging.debug(XMLs.new_podcasts)
            # and an empty line or two for padding & readability
            logging.debug("\n\n\n")
            # And now generate the Podcast feeds
            GENERATE.add_new_episodes(XMLs.new_podcasts, podcast_dir, podcast_feed_dir)
            logging.info("Scan complete")
        else:
            logging.info("No new podcasts found")
        # N
        
        self.amActive = False

# /end iPodcasts()
#-------------------------------------------------------------------------#

# Construct the podcast scheduler
PodcastScheduler = SCHEDULER.Scheduler(iPodcasts(), cycleTime=scan_interval, threadName="PodcastScheduler")

# Run the podcast scheduler
PodcastScheduler.run()