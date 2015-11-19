import xml.etree.ElementTree as ET
import dateutil.parser
from subprocess import Popen, PIPE, STDOUT
import datetime
import time
import logging

# Set up logging
logging.basicConfig(filename="generate_podcast_xml.log", format="%(levelname)s: %(asctime)s: %(message)s", level=logging.DEBUG)

# Import the variables from the other files
from scan_for_xml import *
from scan_for_podcasts import *

# Setting this variable for now. Will need to pass the path to it from a script which checks for new .mp3 and .xml files.
# TO DO: Loop over array
XML_file = new_podcasts['Friction'][0]['xml']

show_tree = ET.parse(XML_file)
show_root = show_tree.getroot()


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

    pub_time_figs = list(timestring)
    pub_time = ''
    pub_offset = ''
    pub_time_data = {}
    for i in range(0,19):
        pub_time += pub_time_figs[i]
    if len(pub_time_figs) == 19:
        pub_offset = pub_time_figs[19]
    elif len(pub_time_figs) == 25:
        for j in range(0,6):
            pub_offset += pub_time_figs[j+19]
    #else:
        # Need to add this
        # TO DO: Whatever I'm doing here? Not sure what this else statement was meant to do
        #print len(pub_time_figs)
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

    length_shell_command = "ffmpeg -i '" + file_path + "' 2>&1 | awk '/Duration/{print $2}'"
    run_length_cmd = Popen(length_shell_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    stdout, stderr = run_length_cmd.communicate()
    # TO DO: Check that the user running the script can access the ffmpeg command.
    #           - When script is run through TextMate, cannot access ffmpeg. With 2>&1 we have stdout = ''
    #             Removing 2>&1 from the shell command will give an error, e.g. "sh: ffmpeg: command not found"
    #print stdout
    #print stderr
    # Check the command ran properly
    if (stdout != '') & (stderr != "None"):
        length_output = stdout[:-2]
    else:
        if not stdout:
            print "There was no output from checking the lenght with ffmpeg. Check the shell command."
            exit()
        if stderr != "None":
            print "There was an error:"
            print stderr
# Now that we've out the output, we have to convert it to seconds, as it is
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

#def add_new_podcast(new_data, podcast_list):
#-------------------------------------------------------------------------#
# This function cycles through the new podcast xml data generated in the 
# script and appends it to the xml file with the appropriate tags.
# new_data is the data generated from the show's xml file.
# podcast_list is the appropriate podcast xml file.
    


#    else:
#    	print ep.tag, ep.text
#for schild in podcast_root:
#	print schild.tag
#	for scchild in schild:
#		for ep in scchild:
#			print ep.tag, ep.attrib, ep.text

# Create the dictionary for the new podcast's tag data
new_data = {}
# The enclosure tag will have attributes rather than text values, so we'll put the in an embedded dictionary.
new_data['enclosure'] = {}

for show_data in show_root:
    # For some reason each .tag value includes {http://linuxcentre.net/xmlstuff/get_iplayer} before the actual value of the tag.
    # Couldn't find out why this is, so I use .split('}',1)[-1] to split the string at the first right hand brace, and return what's to the
    # left of the }. Messy, but it works.
    if show_data.tag.split('}',1)[-1] == 'filename':
        #file_location = show_data.text
        # TO DO: set to looped value
        file_location = new_podcasts['Friction'][0]['mp3']
        new_url = file_location # 'http://192.168.1.84/radio_podcasts/' + file_location.strip('/mnt/Ridcully/Media/Radio/')
        new_data['guid'] = new_url
        new_data['enclosure']['url'] = new_url
        # Now we get the length of the file
        new_length = get_length(file_location)
        new_data['enclosure']['duration'] = new_length
    elif show_data.tag.split('}',1)[-1] == 'episode':
        new_data['title'] = show_data.text
    elif show_data.tag.split('}',1)[-1] == 'desclong':
        new_data['description'] = show_data.text
    elif show_data.tag.split('}',1)[-1] == 'descshort':
        new_data['subtitle'] = show_data.text
        new_data['summary'] = show_data.text
    elif show_data.tag.split('}',1)[-1] == 'firstbcast':
        # pass the first broadcast date through the date formatting function
        new_pub_time = get_pub_time(show_data.text)
        # now parse the date
        # TO DO: add the UTC offset
        new_data['pubDate'] = dateutil.parser.parse(new_pub_time['pub_time'])
    elif show_data.tag.split('}',1)[-1] == 'channel':
        new_data['author'] = show_data.text
    elif show_data.tag.split('}',1)[-1] == 'categories':
        new_data['keywords'] = show_data.text # Might need cleaning up
#    elif show_data.tag.split('}',1)[-1] == '':
#        new_data['explicit'] = 

#for keys,values in new_data.items():
#    print keys + ": => " + str(values)

# Open the xml file for each podcast and add the new tags to it
for pod_title,pod_nums in new_podcasts.items():
    #print pod_title # Title of the podcast
    # Just setting the variable for now; will do in a loop later
    podcast_list = "podcasts_" + pod_title + ".xml"
    #for pod_num,pod_details in pod_nums.items():
        #print pod_num # Number of new podcasts
    #    for f_type,pod_f_path in pod_details.items():
            # info on the podcast: .xml and .mp3 file paths
            #print "\t" + f_type + ": => " + pod_f_path

#podcast_list = new_podcasts['Friction'][0]['mp3']
podcast_tree = ET.parse(podcast_list)
podcast_root = podcast_tree.getroot()
for podcast_chan in podcast_root:
    # Each podcast episode's info is held within the item tag, which is a child at this level.
    # i.e. the item tag is a subelement of the channel element.
    # We can append a new episode within a new item tag at this stage.
    child = ET.Element('item')
    child.attrib['test'] = "value"
    podcast_root.append(child)
    #for podcast_info in podcast_chan:
    #    if podcast_info.tag == "item":
    #        for podcast_ep_info in podcast_info:
    #            print(podcast_ep_info.tag, podcast_ep_info.text)

#pod_item.append((Element.fromstring('<item type="test">Value</item>')))

'''
for tag,data in new_data.items():
    if tag == 'enclosure':
        child = ET.SubElement(item,tag)
        child.set('url', data['url'], 'length', data['length'])
    else:
        child = ET.SubElement(item,tag)
        child.text = data
    #for ep in podcast_root[0]:
    #    if ep.tag == 'item':
    #        print "These are the podcast's details:\n"
    #        for ep_details in ep:           
    #            print ep_details.tag, ep_details.text
#    return true
'''