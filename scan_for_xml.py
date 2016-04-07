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
import json

new_podcasts = {}
ep_num = 0
file_suffixes = ['mp3', 'xml', 'jpg', 'ignore'] # Files we types we want!

# Set the log
logger = logging.getLogger("iPodcasts." + __name__)

def gen_podcast_array(new_podcasts, podcast_title, thisDir, filename):
#-------------------------------------------------------------------------#
# This function generate the new_podcasts dictionary, which itself contains
# several dictionaries. I've used a function to do this as I need to run
# loops I can't while walking through the dictionary. I had a choice of 
# placing the xml/mp3 files in a temporary dictionary and then assigning
# them to the new_podcasts dictionary, or by using this function and the 
# ep_num global variable which gets increased or reset as appropriate.

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".gen_podcast_array")

    global ep_num
    if podcast_title in new_podcasts.keys():
        new_podcasts[podcast_title][ep_num] = {}
        new_podcasts[podcast_title][ep_num]["mp3"] = thisDir + "/" + filename.replace('.xml','.mp3')
        new_podcasts[podcast_title][ep_num]["xml"] = thisDir + "/" + filename
        logger.info("Added new episode to " + podcast_title + ": " + filename.replace('.xml',''))
    else:
        ep_num = 0
        new_podcasts[podcast_title] = {}
        new_podcasts[podcast_title][ep_num] = {}
        new_podcasts[podcast_title][ep_num]["mp3"] = thisDir + "/" + filename.replace('.xml','.mp3')
        new_podcasts[podcast_title][ep_num]["xml"] = thisDir + "/" + filename
        logger.info("Added new pod title: " + podcast_title)
        logger.info("Added new episode to " + podcast_title + ": " + filename.replace('.xml',''))        
    ep_num += 1

# /end add_new_episodes()
#-------------------------------------------------------------------------#

def podcast_walk(directory):
#-------------------------------------------------------------------------#
# Walks the podcast dir

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".podcast_walk")
    
    # Make sure the "to_ignore" list is empty:
    to_ignore = []
    
    for (thisDir, subdirs_found, files_found) in os.walk(directory):
        for filename in files_found:
            
            # Check for the .xml file, and that we're not ignoring it for whatever reason
            if filename.endswith('.xml') & os.path.isfile(thisDir + "/" + filename.replace('.xml','.ignore')):
                # Add the show to the list of files to ignore, checking if it's a radio show and
                # including the show name if it is:
                if ("/" in thisDir.replace(directory,'')) and ("Season_" not in thisDir.replace(directory,'')):
                    # Okay, is a radio show, so add this to the filename to ignore:
                    to_ignore.append(thisDir.replace(directory,'').split('/', 1)[1] + "/" + filename[:-4])
                    logger.debug("There's a file " + thisDir.replace(directory,'').split('/', 1)[1] + "/" + filename[:-4] + ", but we're ignoring it")
                else:
                    to_ignore.append(filename[:-4])
                    logger.debug("There's a file " + filename[:-4] + ", but we're ignoring it")
                # Move to the next item
                continue
            # Now check if there's an .mp3 file without an .xml file
            elif filename.endswith('.mp3') & (os.path.isfile(thisDir + "/" + filename.replace('.mp3','.xml')) == False):
                # Again, add the show to the list of files to ignore (if it's not there already)
                if filename[:-4] not in to_ignore:
                    to_ignore.append(filename[:-4])
                logger.warning("The .mp3 file, " + filename + ", exists but the .xml file does not")
                # Move to the next item
                continue
            # Now check if there's an .xml without a corresponding mp3 file exists
            elif filename.endswith('.mp3') & (os.path.isfile(thisDir + "/" + filename.replace('.xml','.mp3')) == False):
                # Again add the show to the list of files to ignore (if it's not there already)
                if filename[:-4] not in to_ignore:
                    to_ignore.append(filename[:-4])
                logger.warning("The .xml file, " + filename + ", exists but the .mp3 file does not")
                # Move to the next item
                continue
            # And finally, if it's some other type of file (i.e. a partially downloaded or transcoded file), ignore it as well
            elif (filename.rsplit('.',1)[1] not in file_suffixes) or ("partial" in filename):
                # Add the show ...
                if filename.rsplit('.',1)[0] not in to_ignore:
                    to_ignore.append(filename.rsplit('.',1)[0])
                logger.debug("The file, " + filename + ", is not of a type we want, ignoring it")
                # Move to the next item
                continue
            
            # Now add the episode...
            if filename.endswith('.xml') and (filename[:-4] not in to_ignore):
                # Make sure there's a trailing /
                if directory.endswith("/"):
                    podcast_dir = directory
                else:
                    podcast_dir = directory + "/"

                # Seasons can cause a problem with finding the podcast title. We might be in a season subfolder, not
                # in the podcast's home directory. Another problem is generated by radioplays being held as podcasts.
                # They can be saved in the format: Author/Play Title, i.e. Terry Pratchett/Guards Guards. It would be 
                # impractical to have a list of shows like this, so we'll try a dynamic way, which should work for both
                # seasons and shows.
                # First look to see if we're in a subdirectory. Then look if this is a season subdirectory of play title.
                # Finally: remove the Season XX, or set the podcast name to the play title.
                if "/" in thisDir.replace(directory,''):
                    # Okay, we're in a subdirectory, lets find out which type. Is it a Season one?
                    if "Season_" in thisDir.replace(directory,''):
                        podcast_title = thisDir.rsplit('/', 2)[1].replace(' ', '_')
                        logger.debug("Found \"Season\" in the podcast directory; removed.")
                        #                       Replace the podcast directory from this directory
                        #                                                           Now split it at the / between the 
                        #                                                           parent (show title) directory and
                        #                                                           the Season XX directory. Take the
                        #                                                           parent directory as the podcast_title
                    else:
                        podcast_title = thisDir.replace(directory,'').split('/', 1)[1].replace(' ', '_')
                        logger.debug("This podcast is part of a radio play.\nFull path is: " + thisDir + "\nSetting the podcast title to the play title: " + podcast_title)
                        #                       Replace the podcast directory from this directory
                        #                                                           Now split it at the / between the 
                        #                                                           parent (show title) directory and
                        #                                                           the play title directory. Take the
                        #                                                           play title directory as the podcast_title
                else:
                    podcast_title = thisDir.replace(directory,'').replace(' ', '_')
                # .replace(' ', '_') at the end of all podcast titles so that there are no spaces in the xml file names

                logger.info("The .mp3 and .xml for the new podcast episode for " + filename[:-4] + " both exist, continuing ...")
                gen_podcast_array(new_podcasts, podcast_title, thisDir, filename)
            # Else: it's some other type of file, so move on
            
    # If there are any episodes to ignore, log that to INFO.
    # Note: ignored files are logged to DEBUG
    if to_ignore:
        logger.info("Some files were ignored. Set log level to DEBUG for more information on which files were ignored.")

if __name__ == "__main__":
    podcast_walk()