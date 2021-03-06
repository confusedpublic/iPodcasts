# For xml processing & parsing for BeautifulSoup
from lxml import etree as ET
# For getting the length of the mp3
from subprocess import Popen, PIPE, STDOUT
# For date related activities
import datetime
from dateutil.tz import tzlocal
import time
# For Logging
import logging
# For checking file exists
import os
# For web scraping
from bs4 import BeautifulSoup
import urllib2
# For parsing and altering the settings file
import json
# For scheduling the scan
import threading
# For loggin the traceback errors, if any, from the scheduling via threading
import traceback

# Needed for the owner's email address in the podcast's xml file.
EMAIL = 'dave.race@gmail.com'

# Set the log
logger = logging.getLogger("iPodcasts." + __name__)

def get_pub_time(timestring):
#-------------------------------------------------------------------------#
# This function formats the first published date from the get_iplayer xml 
# file, which is in the ISO8601 format (set in the get_iplayer preferences).
# This format includes a UTC offset at the end, which can be inconvenient,
# as there doesn't seem to be any good way of handling the off sets.
# 
# The function splits the time into a list for each character, then combines
# the first 18 figures to produce the time and the last 1 to 6 figures to 
# produce the off set (it's either Z or +00:00).
#
# e.g. 2015-11-26T04:00:00Z is split into a list: (2, 0, 1, 5 ...)
# The first 19 characters form the time (2015-11-26T04:00:00), and the last
# character (Z) forms the off set.    

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".get_pub_time")

    pub_time_figs = list(timestring)
    pub_time = ''
    pub_offset = ''
    pub_time_data = {}
    for i in range(0,19):
        pub_time += pub_time_figs[i]
    if len(pub_time_figs) == 20:
        pub_offset = pub_time_figs[19]
    elif len(pub_time_figs) == 25:
        for j in range(0,6):
            pub_offset += pub_time_figs[j+19]
    else:
        logger.error("The published time was a different length string than expected.\nPublished time was: " + timestring + "; this is " + str(len(timestring)) + " characters long")
    pub_time_tmp = datetime.datetime.strptime(pub_time, "%Y-%m-%dT%H:%M:%S")
    pub_time = datetime.datetime.strftime(pub_time_tmp, "%a, %d %b %Y %H:%M:%S GMT") # %Z empty, should be GMT. TO DO: FIX
    pub_time_data['pub_time'] = pub_time
    pub_time_data['pub_offset'] = pub_offset
    return pub_time_data

# /end get_pub_time()
#-------------------------------------------------------------------------#

def get_length(file_path):
#-------------------------------------------------------------------------#
# Unfortunately get_iplayer does not report a correct length for the 
# podcasts. To fix this we need to look at the actual file. An easy way of
# doing this is to use the ffmpeg -i (info) shell command (as we use ffmpeg 
# with get_iplayer anyway. We simply run the command, awk the output for 
# the duration (which contains a trialing ',', which we can trim off) and 
# return the length in seconds from the function.
#
# While this is simple enough to *do*, it was a bit of a nightmare to get 
# *working*. Basically, in order to use pipes and awk the output of the 
# ffmpeg command, you have to have the shell=True option. This also lets
# the command be a string. Otherwise you have to run the command as a
# list, where each command, flag, argument, etc. is a different item in 
# the list.
# Also, because we're running the subprocess.check_output function as 
# shell=True, we get a '\n' on the end of our string, so we have to cut that
# off as well. 

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".get_length")
    
    length_shell_command = "ffmpeg -i '" + file_path + "' 2>&1 | awk '/Duration/{print $2}'"
    run_length_cmd = Popen(length_shell_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    stdout, stderr = run_length_cmd.communicate()
    # TO DO: Check that the user running the script can access the ffmpeg command.
    #           - When script is run through TextMate, cannot access ffmpeg. With 2>&1 we have stdout = ''
    #             Removing 2>&1 from the shell command will give an error, e.g. "sh: ffmpeg: command not found"

    # Check the command ran properly
    if (stdout != '') & (stderr != "None"):
        length_output = stdout[:-2]
    else:
        if not stdout:
            logger.error("There was no output from checking the lenght with ffmpeg. Check the shell command.")
            exit()
        if stderr != "None":
            logger.error("There was an error:")
            logger.error("stderr")
    
    # Now that we've got the output, we have to convert it to seconds, as it is
    # in the HH:MM:SS format.

    t = time.strptime(length_output,'%H:%M:%S.%f')
    podcast_length = datetime.timedelta(hours=t.tm_hour,minutes=t.tm_min,seconds=t.tm_sec).total_seconds()

    # Finally, because the timedelta & total_seconds functions return the seconds 
    # with a trailing .0, we'll cut that off, after first converting the datetime
    # object into a string.

    podcast_length = str(podcast_length)[:-2]

    # Done, finally! Now just return the value for the length of the podcast

    return podcast_length

# /end get_length()
#-------------------------------------------------------------------------#

def get_desc(page):
#-------------------------------------------------------------------------#
# Scrape the BBC website for the show's general description.
# We look for the following tags:
# <div class="map__intro__synopsis centi" property="description">
#   <p> -example desc- </p>
# </div>

    file = urllib2.urlopen(page)
    soup = BeautifulSoup(file, "lxml")
    desc = soup.find(property='description')
    return str(desc.string)

# /end get_desc()
#-------------------------------------------------------------------------#


def create_new_podcast(podcast_xml_file, podcast_list):
#-------------------------------------------------------------------------#
# This function is called if the podcast does not currently have a
# podcast xml file. It then creates the xml file with the appropriate
# general tags.
#
# Need to generate the following xml tags from the show data:
#   <title> - Podcast title taken from the show title
#   <link> - Link to the show's page on the BBC website
#   <ns0:owner>
#       <ns0:name> - Title of the show again    
#   <ns0:keywords/> - Keywords for searching, if there are any
#   <copyright> - Copyright for the BBC
#   <ns0:image href=""/> - Image for the podcast
#   <ns0:author - Author of the podcast, set to the radiostation it was broadcast from
#   <image> - Parent tag for image information, set statically.
#       <title> - Title of the show again
#       <url> - Image for the podcast, again
#       <link> - Link to the show's page on the BBC website again
#
# And need to create the following xml tags which are static/not dependant 
# upon the show's xml
#   <language> - Language the show is in (default set to 'en-gb')
#   <ttl>15</ttl> - Don't know what this tag is for. Set to a random number for now, 
#                   will test what changing it does.
#   <lastBuildDate> - Last time the podcast xml file was generated
#   <ns0:owner>
#       <ns0:email> - the email of the podcast xml file - set this as your own email
#   <ns0:explicit> - Whether the show has explicit content or not (default set to 'no')
#
# Unfortunatley, the descriptions in the xml file are specific to the episode. To get 
# the general description of the show for the following tags, we'll have to do a quick
# bit of web scraping.
#   <description> - Description of the show
#   <ns0:summary> - Summary of the show (same as description)
# We can find the link to the programme's website from the xml file and plug it into a function
# to find the information we need to make this code easier to ride & to split tasks.

#
# The podcast xml file comes through in the form: podcast_feed_dir + "podcasts_" + pod_title + ".xml"
# This means we already know where, and with what name to create it.
# We will need to look up one of the xml files from the downloaded episodes, though,
# to scrape the general information.

#The easiest way to do this is to cycle through the 
# podcast_list dictionary and see if one of the pod_titles is in the podcast_xml_file string
# then pick the first episode's (i.e. index 0) xml file.
#
#

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".create_new_podcast")

    # Namespace set up
    pod_ns = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    pod_ns_tag = "{%s}" % pod_ns
    pod_ns_key = "itunes"
    # And generate the namespace map for turning the literal namespace into the key/abbreviation later
    NSMAP = {pod_ns_key: pod_ns}
    # Build a list of tags which use the namespaces
    needs_namespaces = ['owner', 'name', 'email', 'image', 'author', 'explicit', 'summary']

    # ------------------------------
    # Set up the static tags

    # lastBuildDate requires the current time.
    # datetime.now() returns an empty value for the local time zone. I found how to produce 
    # a timeszone from here, http://joelinoff.com/blog/?p=802, using tzlocal()
    now = datetime.datetime.now(tzlocal())
    now = datetime.datetime.strftime(now, "%a, %d %b %Y %H:%M:%S %Z")

    new_show = {'explicit': 'no', 'owner': {'email': EMAIL}, 'lastBuildDate': now, 'language': 'en-gb', 'ttl': 10, 'image_p': {}}
    
    # TO DO:
    # Change the loop here.
    # Current behaviour: checks if current pod_title is the file we're looking at; will cycle through till it finds a title that matches
    # Desired behaviour: takes the file we're looking at and looks if it's in the pod_titles we have in the podcast_list
    # i.e. flip around the way we're looking them up.
    # Will require extracting the podcast title from the podcast_xml_file
    # podcast_xml_file = podcast_feed_dir + "podcasts_" + pod_title + ".xml"
    """"
    for pod_title, pod_num in podcast_list.items():
        # This looks to see if the podcast title is any string in the list
        if pod_title in podcast_xml_file:
            # If it is, we only need the first episode's xml file (and there may only be 1 episode anyway)
            # so grab that and break the loop.
            new_ep_xml = podcast_list[pod_title][0]['xml']
            break
        else:
            # Utoh, didn't find it. That means there'll be no xml files and something's gone wrong.
            logger.error("Can't find the podcast " + pod_title + " in the podcast lists.")
    """
    pod_title = podcast_xml_file.rsplit('/',1)[1][9:-4] # Get the xml file from the xml file path, and strip 
    #                                                     'podcast_' and '.xml' from this string to get the title
    if pod_title in podcast_list:
        new_ep_xml = podcast_list[pod_title][0]['xml']
    else:
        # Utoh, didn't find it. That means there'll be no xml files and something's gone wrong.
        logger.error("Can't find the podcast " + pod_title + " in the podcast lists.")
        logger.error("The podcast title, \"" + pod_title + "\", was taken from the xml file path: " + podcast_xml_file)
          
    # Bit of error checking.
    # Check the variable was assigned, i.e. that the podcast was found in the list
    if "new_ep_xml" not in locals():
        logger.error("The podcast wasn't found at all in the podcast lists. Aborting.")
        exit()
    # Check the file exists
    if os.path.isfile(new_ep_xml) == False:
        logger.error("The first episode .xml file doesn't actually exist. Exited.\nxml file was: " + new_ep_xml)
        exit()

    # Open the file and get the information out.
    show_tree = ET.parse(new_ep_xml)
    show_root = show_tree.getroot()
    # now loop over it to get the podcast episode's information and put it in a new array
    for show_data in show_root:
        # Each .tag value includes the namespace {http://linuxcentre.net/xmlstuff/get_iplayer} before the actual value of the tag.
        # I used .split('}',1)[-1] to split the string at the first right hand brace, and return what's to the
        # left of the }. Messy, but it works.
        if show_data.tag.split('}',1)[-1] == 'name':
            new_show['title'] = show_data.text
            new_show['owner']['name'] = show_data.text
            new_show['image_p']['title'] = show_data.text
        elif show_data.tag.split('}',1)[-1] == 'web':
            new_show['link'] = show_data.text
            new_show['image_p']['link'] = show_data.text
            new_show['description'] = get_desc(show_data.text)
            new_show['summary'] = get_desc(show_data.text)
        elif show_data.tag.split('}',1)[-1] == 'thumbnail':
            new_show['image'] = show_data.text
            new_show['image_p']['url'] = show_data.text
        elif show_data.tag.split('}',1)[-1] == 'channel':
            new_show['author'] = show_data.text
        elif show_data.tag.split('}',1)[-1] == 'categories':
            new_show['keywords'] = show_data.text
        elif show_data.tag.split('}',1)[-1] == 'category':
            new_show['category'] = show_data.text
        elif show_data.tag.split('}',1)[-1] == 'firstbcast':
            # Get the first 4 characters of the first published date which is in the format
            # YYYY-MM-DDTHH:MM:SSz
            cr_year = show_data.text[:4]
            new_show['copyright'] = "BBC &#169; " + cr_year
   
    # Now make the file:
    new_xml_file = open(podcast_xml_file, "w")
    # Close the file
    new_xml_file.close
    logger.info("Created the new file: " + podcast_xml_file)

    # Build the xml tree
    podcast_root = ET.Element("rss", nsmap=NSMAP)
    podcast_root.attrib['version'] = "2.0"
    channel = ET.SubElement(podcast_root, "channel")

    for tag, text in new_show.items():
        if tag in needs_namespaces:
            # We'll the namespace literal to the tag
            # Different for the image tag, thoguh, as it has an attribute, not text.
            ns_tag = pod_ns_tag + tag
            show_child = ET.SubElement(channel, ns_tag, nsmap=NSMAP)
            if tag == "image":
                show_child.attrib['href'] = text
            elif tag == "owner":
                for child_tag, child_text in text.items():
                    ns_tag = pod_ns_tag + child_tag
                    show_child_child = ET.SubElement(show_child, ns_tag, nsmap=NSMAP)
                    show_child_child.text = child_text
            else:
                show_child.text = text
        else:
            if tag == "image_p":
                show_child = ET.SubElement(channel, "image")
                for child_tag, child_text in text.items():
                    show_child_child = ET.SubElement(show_child, child_tag)
                    show_child_child.text = child_text
            else:
                show_child = ET.SubElement(channel, tag)
                show_child.text = str(text)
            
    # And write the xml to the file
    podcast_tree = ET.ElementTree(podcast_root)
    with open(podcast_xml_file, "w") as f:
        logger.info("Adding the new xml to the file: " + podcast_xml_file)
        podcast_tree.write(f, pretty_print=True)

# /end create_new_podcast()
#-------------------------------------------------------------------------#

def gen_webpage(podcast_feed_dir):
#-------------------------------------------------------------------------#
# Generate & update the webpage for subscription links for iTunes podcasts
    
    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".gen_webpage")
    
    podcast_feed_links = {}
        
    # Open the directory and walk through all the xml files:
    for (thisDir, subdirs_found, files_found) in os.walk(podcast_feed_dir):
        for filename in files_found:
            if ".xml" in filename: # Just to be sure we're only grabbing xml files
                podcast_feed_links[filename[:-4]] = 'pcast://192.168.1.84/podcasts/' + filename
    
    # Make the file if it doesn't exist:
    html_file = podcast_feed_dir + 'index.html'
    if not os.path.exists(html_file):
        new_html_file = open(html_file, "w") 
        # Close the file
        new_html_file.close
        logger.info("Created the new html file: " + html_file)

        # Build the html document
        html_root = ET.Element("html")
        html_head = ET.SubElement(html_root, "head")
        title = ET.SubElement(html_head, "title")
        title.text = "iTunes Podcast Feeds"
        html_body = ET.SubElement(html_root, "body")
        for pod_title, file in podcast_feed_links.items():
            html_p = ET.SubElement(html_body, "p")
            feed_link = ET.SubElement(html_p, "a")
            feed_link.attrib['href'] = file
            feed_link.text = "Subscribe to " + pod_title + " podcast in iTunes"
            logger.info("Added a subscription link for the podcast: " + pod_title)
        
        html_tree = ET.ElementTree(html_root)
        with open(html_file, "w") as f:
            logger.info("Opened " + html_file + " to write html")
            html_tree.write(f, pretty_print=True)
    else:
        logger.info("Opening the " + html_file + " file for html parsing")
        parser = ET.XMLParser(remove_blank_text=True)
        html_tree = ET.parse(html_file, parser)
        html_root = html_tree.getroot()
        
        # Not sure this works! Where's "file" and "pod_title" coming from here?!
        for links in html_tree.iterfind('a'):
            if links.attrib[href] not in podcast_feed_links.values():
                feed_link = ET.SubElement("p", "a")
                feed_link.attrib['href'] = file
                feed_link.text = "Subscribe to " + pod_title + " podcast in iTunes"
                logger.warning("Just added title \"" + pod_title + "\" to the html podcast feeds page")
                
        html_tree = ET.ElementTree(html_root)
        with open(html_file, "w") as f:
            logger.info("Opened " + html_file + " to write html")
            html_tree.write(f, pretty_print=True)


# /end gen_webpage()
#-------------------------------------------------------------------------#

def tidy_episode_title(episode_title):
#-------------------------------------------------------------------------#
# get_iplayer has a bad habbit of finding episode titles with the episode 
# number preceeding the actual title, e.g. "3. Episode 3". This function
# checks whether this is the case, and then removes it if so.
#
# I've attempted to write a check into the function, but it is possible
# that a future version of get_iplayer alters how it names files, or that
# one setting alters this, this is might not always work in the future.
#
# If the format check fails, I'll just return the episode title as the 
# function is passed it so that the programme doesn't exit.

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".tidy_episode_title")
    
    # Split the title and get the parts into the appropriate variables
    title_parts = episode_title.split(" ")
    preceding_number = title_parts[0].strip(".") # Remove the . after number
    end_number = title_parts[-1]
    
    # Check the episode title format is as we expect:
    if preceding_number != end_number:
        # The values we found don't match, most likely the title doesn't have an episode number
        # Log this problem for debugging
        logging.debug("The values for the preceding and ending episode numbers do not match. Check the episode title. It was: " + episode_title)
        
        # Return the episode title we were passed
        return episode_title
    else:
        sep = " " # Separator for the join method
        # Okay, they match, so lets remove the starting one by rewriting the episode title:
        episode_title = sep.join(title_parts[1:])
    
        return episode_title
    
    

# /end tidy_episode_title()
#-------------------------------------------------------------------------#

def add_new_episodes(podcast_list, podcast_dir, podcast_feed_dir):
#-------------------------------------------------------------------------#
# This function cycles through the new podcast xml data generated in the 
# script and appends it to the xml file with the appropriate tags.
# new_data is the data generated from the show's xml file.
# podcast_list is the appropriate podcast xml file.

# TO DO:
# Add line to atler the podcast image to the new episode's image?

    # Set the log
    logger = logging.getLogger("iPodcasts." + __name__ + ".add_new_episodes")
    
    # Create the dictionary for the new podcast's tag data
    new_data = {}
    # Create the list of new podcasts
    podcast_xmls = []

    for pod_title, pod_num in podcast_list.items():
        new_data[pod_title] = {}
        for pod_number, pod_details in pod_num.items():
            new_data[pod_title][pod_number] = {}
            # The enclosure tag will have attributes rather than text values, so we'll put the in an embedded dictionary.
            new_data[pod_title][pod_number]['enclosure'] = {'type': "audio/mpeg"}
            # get_iplayer's output xml file doesn't seem to have an explicit tag, so we'll set it as no by default
            new_data[pod_title][pod_number]['explicit'] = "no"
            # set the variables for the current podcast xml and mp3 file
            XML_file = podcast_list[pod_title][pod_number]['xml']
            MP3_file = podcast_list[pod_title][pod_number]['mp3']
            # open the podcast episode's xml file
            show_tree = ET.parse(XML_file)
            show_root = show_tree.getroot()
            # now loop over it to get the podcast episode's information and put it in a new array
            for show_data in show_root:
                # Each .tag value includes the namespace {http://linuxcentre.net/xmlstuff/get_iplayer} before the actual value of the tag.
                # I used .split('}',1)[-1] to split the string at the first right hand brace, and return what's to the
                # left of the }. Messy, but it works.
                if show_data.tag.split('}',1)[-1] == 'filename':
                    show_data.text = 'http://192.168.1.84/radio_podcasts/' + MP3_file.strip(podcast_dir)
                    new_data[pod_title][pod_number]['guid'] = show_data.text
                    new_data[pod_title][pod_number]['enclosure']['url'] = show_data.text
                    # Now we get the length of the file
                    new_length = get_length(MP3_file)
                    new_data[pod_title][pod_number]['enclosure']['duration'] = new_length
                    # Now convert the length in seconds to the time in hh:mm:ss for the duration tag
                    new_data[pod_title][pod_number]['duration'] = str(datetime.timedelta(seconds=int(new_length)))
                elif show_data.tag.split('}',1)[-1] == 'episode':
                    new_data[pod_title][pod_number]['title'] = tidy_episode_title(show_data.text)
                elif show_data.tag.split('}',1)[-1] == 'desclong':
                    new_data[pod_title][pod_number]['description'] = show_data.text
                elif show_data.tag.split('}',1)[-1] == 'descshort':
                    new_data[pod_title][pod_number]['subtitle'] = show_data.text
                    new_data[pod_title][pod_number]['summary'] = show_data.text
                elif show_data.tag.split('}',1)[-1] == 'firstbcast':
                    # pass the first broadcast date through the date formatting function
                    new_pub_time = get_pub_time(show_data.text)
                    # now parse the date
                    # TO DO: add the UTC offset
                    new_data[pod_title][pod_number]['pubDate'] = new_pub_time['pub_time']
                elif show_data.tag.split('}',1)[-1] == 'channel':
                    new_data[pod_title][pod_number]['author'] = show_data.text
                elif show_data.tag.split('}',1)[-1] == 'categories':
                    new_data[pod_title][pod_number]['keywords'] = show_data.text # Might need cleaning up

    # Create a list of the XML files for each podcast
    for pod_title, pod_nums in podcast_list.items():
        podcast_xmls.append(podcast_feed_dir + "podcasts_" + pod_title + ".xml")
    # Check that these files exist, and if not (i.e. we have a new podcast), call the create_new_podcast() function
    # to make the XML file.
    for xml_file in podcast_xmls:
        if os.path.isfile(xml_file) == False:
            create_new_podcast(xml_file, podcast_list)

    # To print the XML with proper indentation, need to remove the whitespace first,
    # as outlined in the accepted answere here: http://stackoverflow.com/questions/7903759/pretty-print-in-lxml-is-failing-when-i-add-tags-to-a-parsed-tree
    for podcasts in podcast_xmls:
        podcast = podcasts.split("podcasts_")[1][:-4]
        logger.info("Opening the " + podcasts + " file for xml parsing")
        parser = ET.XMLParser(remove_blank_text=True)
        podcast_tree = ET.parse(podcasts, parser)
        podcast_root = podcast_tree.getroot()

        # Get the xml namespace from the current file
        podcast_ns = podcast_root.nsmap
        for abbrv, uri in podcast_ns.items():
            pod_ns_key = abbrv
            pod_ns = uri
        # Now format it for later; the namespace has to be in the {uri} form
        pod_ns_tag = "{%s}" % pod_ns
        # And generate the namespace map for turning the literal namespace into the key/abbreviation later
        NSMAP = {pod_ns_key: pod_ns}
        # The iTunes podcast xml file has namespaces for the tags held in the namespace list below.
        needs_namespaces = ['duration', 'author', 'explicit', 'keywords', 'subtitle', 'summary']

        for elm in podcast_tree.iterfind('channel'):
            # Each podcast episode's info is held within the item tag, which is a child of the channel tag.
            # channel is the elm of this loop, which lets us append a new item tag as a child of elm.
            # We can then run through each part of the show_data dictionary to add the tags for the new episode
            for num, new_xml in new_data[podcast].items():
                item = ET.SubElement(elm, 'item')
                for tag, text in new_xml.items():
                    if tag == "enclosure":
                        show_child = ET.SubElement(item, tag)
                        for att, val in text.items():
                            show_child.attrib[att] = val
                    elif tag in needs_namespaces:
                        # Add the namespace literal to the tag
                        ns_tag = pod_ns_tag + tag
                        show_child = ET.SubElement(item, ns_tag, nsmap=NSMAP)
                        show_child.text = text
                    else:
                        show_child = ET.SubElement(item, tag)
                        show_child.text = text
        
        # Now that we've finished adding the episode, alter the last build date of the xml file to now()
        now = datetime.datetime.now(tzlocal())
        now = datetime.datetime.strftime(now, "%a, %d %b %Y %H:%M:%S %Z")       
        for elm in podcast_tree.find('channel'):
            if elm.tag == "lastBuildDate":
                elm.text = str(now)
        logger.info("Updated the lastBuildDate tag to now: " + now)
                        
        # Write the xml tree to the file
        podcast_tree = ET.ElementTree(podcast_root)
        with open(podcasts, "w") as f:
            logger.info("Opened " + podcasts + " to write xml")
            podcast_tree.write(f, pretty_print=True)

    # Now that we've added the data for each new podcast, we need to create a .ignore file
    # for each podcast. This is simple & straight forward.
    for pod_title, pod_num in podcast_list.items():
        for pod_number, pod_details in pod_num.items():
            ignore_file_path = pod_details['xml'][:-4] + ".ignore"
            ignore_file = open(ignore_file_path, "w")
            ignore_file.close
            if os.path.isfile(ignore_file_path) == True:
                logger.info("Created the .ignore file for podcast: " + pod_details['xml'][:-4])
            else:
                logger.error("Something went wrong creating the .ignore file for the podcast: "  + pod_details['xml'][:-4])
            
    logger.info("Finished adding new podcast episodes")
    
    logger.info("Now generating the new webpage...")
    
    gen_webpage(podcast_feed_dir)

# /end add_new_episodes()
#-------------------------------------------------------------------------#

if __name__ == "__main__":
    add_new_episodes()