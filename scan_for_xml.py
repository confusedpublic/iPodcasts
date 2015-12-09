#-------------------------------------------------------------------------#
#                                                                         #
#                         scan_for_xml.py                                 #
#                                                                         #
#-------------------------------------------------------------------------#
#                                                                         #
# This is another simple script which is called if do_scan is returned    #
# true. This scans the relevant podcast directory (found in the config    #
# file) for new xml files. If it finds them, it adds them to a dictionary #
# and creates a .ignore file with the same prefix so that we don't add a  #
# podcast twice. (It also checks for the .ignore file before adding the   #
# xml file to the dictionary of course. I chose this method over keeping  #
# track of the files in an db as the .ignore files can be cleaned out     #
# more easily with the original files                                     #
#                                                                         #
#-------------------------------------------------------------------------#

import os
import logging

def gen_podcast_array(new_podcasts, podcast_title, thisDir, filename):
#-------------------------------------------------------------------------#
# This function generate the new_podcasts dictionary, which itself contains
# several dictionaries. I've used a function to do this as I need to run
# loops I can't while walking through the dictionary. I had a choice of 
# placing the xml/mp3 files in a temporary dictionary and then assigning
# them to the new_podcasts dictionary, or by using this function and the 
# ep_num global variable which gets increased or reset as appropriate.

    global ep_num
    if podcast_title in new_podcasts.keys():
        new_podcasts[podcast_title][ep_num] = {}
        new_podcasts[podcast_title][ep_num]["mp3"] = thisDir + "/" + filename.replace('.xml','.mp3')
        new_podcasts[podcast_title][ep_num]["xml"] = thisDir + "/" + filename
        logging.info("Added new episode to " + podcast_title + ": " + filename.replace('.xml',''))
    else:
        ep_num = 0
        new_podcasts[podcast_title] = {}
        new_podcasts[podcast_title][ep_num] = {}
        new_podcasts[podcast_title][ep_num]["mp3"] = thisDir + "/" + filename.replace('.xml','.mp3')
        new_podcasts[podcast_title][ep_num]["xml"] = thisDir + "/" + filename
        logging.info("Added new pod title to " + podcast_title)
        logging.info("Added new episode to " + podcast_title + ": " + filename.replace('.xml',''))        
    ep_num += 1
    return new_podcasts
    
# /end add_new_episodes()
#-------------------------------------------------------------------------#

# Check for the configuration file
config = open('config', 'r')
lines = config.readlines()
settings = {}
podcast_dir = ''
new_podcasts = {}
ep_num = 0

for line in lines:
    if "podcast_dir" in line:
        setting = line.split(' ',1)
        podcast_dir = setting[1][1:-2] # Need to trim the \n and the " " marks from the path

# Just a quick check before going any further that the directory has been set
if not podcast_dir:
    logging.error("No podcast directory given. Please set this in the config file.")
    exit()
    
# Now check whether it actually exists!
if not os.path.isdir(podcast_dir):
    logging.error("The podcast directory set in the config file does not exist. Please set this to an existing directory.")
    
# Now lets walk through the podcast directory and find all the .xml and .ignore files
for (thisDir, subdirs_found, files_found) in os.walk(podcast_dir):
    for filename in files_found:
        # Check for the .xml file, and that we're not ignoring it for whatever reason
        if filename.endswith('.xml') & os.path.isfile(thisDir + "/" + filename.replace('.xml','.ignore')):
            logging.info("There's a file " + filename + ", but we're ignoring it")
        # Now check if there's an .mp3 file without an .xml file
        # TO DO: will then need to scrape the details for the .xml file from the bbc website. More work to do later
        elif filename.endswith('.mp3') & (os.path.isfile(thisDir + "/" + filename.replace('.mp3','.xml')) == False):
            logging.warning("The .mp3, " + filename + ", exists but the .xml file does not")
        # Check for the .xml file, and check it's not the podcast subscription .xml file
        elif filename.endswith('.xml') & ("podcast" not in filename):
            # Found a new xml file, better check the corresponding mp3 file exists
            if os.path.isfile(thisDir + "/" + filename.replace('.xml','.mp3')):
                podcast_title = thisDir.replace(podcast_dir + "/",'')
                logging.info("The .mp3 and .xml for the new podcast episode for " + podcast_title + " both exist, continuing ...")
                gen_podcast_array(new_podcasts, podcast_title, thisDir, filename)
            else:
                logging.error("The .xml file, " + filename + ", exists but the .mp3 does not")
        # Else: it's some other type of file, so move on