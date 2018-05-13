# -*- coding: utf-8 -*-

from lxml import etree as ET
import datetime
from dateutil.tz import tzlocal
import logging
import os
import copy

from ipodcasts import get_ip, PodcastXML

# Needed for the owner's email address in the podcast's xml file.
email = 'dave.race@gmail.com'

logger = logging.getLogger( __name__)


class PodcastSubscriptionFeedManager(PodcastXML):

    def __init__(self, podcast_dir, podcast_feed_dir):
        self.podcast_dir = podcast_dir
        self.podcast_feed_dir = podcast_feed_dir
        super().__init__(self, email)

    @staticmethod
    def _add_ignore_file(episode_file_path):
        """ Creates a the ignore file so that we don't add the info again
            TODO: replace with a sqlite or similar file based db
        """

        ignore_file_path = episode_file_path.replace('.mp3', '.ignore')
        filename = os.path.splitext(os.path.basename(episode_file_path))[1]

        with open(ignore_file_path, "w") as f:
            pass

        if os.path.isfile(ignore_file_path):
            logger.info("Created the .ignore file for podcast: %s", filename)
        else:
            logger.error("Something went wrong creating the .ignore file for the podcast: %s", filename)

    @staticmethod
    def _format_now(now_dt):

        return datetime.datetime.strftime(now_dt, "%a, %d %b %Y %H:%M:%S %Z")

    def create_new_podcast_feed(self, podcast_data, podcast_feed):
        """ This function is called if the podcast does not currently have a
            podcast xml file. It then creates the xml file with the appropriate
            general tags.

            Need to generate the following xml tags from the show data:
              <title> - Podcast title taken from the show title
              <link> - Link to the show's page on the BBC website
              <ns0:owner>
                  <ns0:name> - Title of the show again
              <ns0:keywords/> - Keywords for searching, if there are any
              <copyright> - Copyright for the BBC
              <ns0:image href=""/> - Image for the podcast
              <ns0:author - Author of the podcast, set to the radiostation it was broadcast from
              <image> - Parent tag for image information, set statically.
                  <title> - Title of the show again
                  <url> - Image for the podcast, again
                  <link> - Link to the show's page on the BBC website again

            And need to create the following xml tags which are static/not dependant
            upon the show's xml
              <language> - Language the show is in (default set to 'en-gb')
              <ttl>15</ttl> - Don't know what this tag is for. Set to a random number for now,
                              will test what changing it does.
              <lastBuildDate> - Last time the podcast xml file was generated
              <ns0:owner>
                  <ns0:email> - the email of the podcast xml file - set this as your own email
              <ns0:explicit> - Whether the show has explicit content or not (default set to 'no')

            Unfortunatley, the descriptions in the xml file are specific to the episode. To get
            the general description of the show for the following tags, we'll have to do a quick
            bit of web scraping.
              <description> - Description of the show
              <ns0:summary> - Summary of the show (same as description)
            We can find the link to the programme's website from the xml file and plug it into a function
            to find the information we need to make this code easier to ride & to split tasks.


            The podcast xml file comes through in the form: podcast_feed_dir + "podcasts_" + pod_title + ".xml"
            This means we already know where, and with what name to create it.
            We will need to look up one of the xml files from the downloaded episodes, though,
            to scrape the general information.

            The easiest way to do this is to cycle through the
            podcast_list dictionary and see if one of the pod_titles is in the podcast_xml_file string
            then pick the first episode's (i.e. index 0) xml file.
        """



        # ------------------------------
        # Set up the static tags

        # lastBuildDate requires the current time.
        # datetime.now() returns an empty value for the local time zone. I found how to produce
        # a timeszone from here, http://joelinoff.com/blog/?p=802, using tzlocal()
        now = self._format_now(datetime.datetime.now(tzlocal()))

        new_show = copy.deepcopy(self.new_show_template)
        new_show.extend(podcast_data)
        new_show['lastBuildDate'] = now

        # Build the xml tree
        podcast_root = ET.Element("rss", nsmap=self.namespace_map)
        podcast_root.attrib['version'] = "2.0"
        channel = ET.SubElement(podcast_root, "channel")

        for tag, text in new_show.items():
            if tag in self.needs_namespaces:
                # We'll the namespace literal to the tag
                # Different for the image tag, thoguh, as it has an attribute, not text.
                ns_tag = self.pod_ns_tag + tag
                show_child = ET.SubElement(channel, ns_tag, nsmap=self.namespace_map)
                if tag == "image":
                    show_child.attrib['href'] = text
                elif tag == "owner":
                    for child_tag, child_text in text.items():
                        ns_tag = self.pod_ns_tag + child_tag
                        show_child_child = ET.SubElement(show_child, ns_tag, nsmap=self.namespace_map)
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
        with open(podcast_feed, "w") as f:
            logger.info("Adding the new xml to the file: " + podcast_feed)
            podcast_tree.write(f, pretty_print=True)

    def add_to_podcast_feed(self, episode_data, podcast_feed):
        """ Add the episode data to the podcast feed's xml file
            TODO: update file with most recent podcast's thumbnail
        """

        logger.info("Opening %s for xml parsing", podcast_feed)
        parser = ET.XMLParser(remove_blank_text=True)
        podcast_tree = ET.parse(podcast_feed, parser)
        podcast_root = podcast_tree.getroot()

        # # Get the xml namespace from the current file
        # podcast_ns = podcast_root.nsmap
        # for abbrv, uri in podcast_ns.items():
        #     pod_ns_key = abbrv
        #     pod_ns = uri
        # # Now format it for later; the namespace has to be in the {uri} form
        # pod_ns_tag = "{%s}" % self.pod_ns
        # # And generate the namespace map for turning the literal namespace into the key/abbreviation later
        # NSMAP = {self.pod_ns_key: self.pod_ns}
        # # The iTunes podcast xml file has namespaces for the tags held in the namespace list below.
        # needs_namespaces = ['duration', 'author', 'explicit', 'keywords', 'subtitle', 'summary']

        for elm in podcast_tree.iterfind('channel'):
            # Each podcast episode's info is held within the item tag, which is a child of the channel tag.
            # channel is the elm of this loop, which lets us append a new item tag as a child of elm.
            # We can then run through each part of the show_data dictionary to add the tags for the new episode
            for num, new_xml in episode_data.items():
                item = ET.SubElement(elm, 'item')
                for tag, text in new_xml.items():
                    if tag == "enclosure":
                        show_child = ET.SubElement(item, tag)
                        for att, val in text.items():
                            show_child.attrib[att] = val
                    elif tag in self.needs_namespaces:
                        # Add the namespace literal to the tag
                        ns_tag = self.pod_ns_tag + tag
                        show_child = ET.SubElement(item, ns_tag, nsmap=self.namespace_map)
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
        with open(podcast_feed, "w") as f:
            logger.info("Opened %s to write xml", podcast_feed)
            podcast_tree.write(f, pretty_print=True)

    @staticmethod
    def find_current_subscription_xmls(podcast_feed_xml_directory):
        
        return os.listdir(podcast_feed_xml_directory)


class PodcastSubscriptionWebPage(object):
    
    def __init__(self, webpage_path):
        self.webpage_path = webpage_path
        self.podcast_links = self._create_podcast_links()
    
    @staticmethod
    def _create_podcast_links(podcast_feed_dir):
        """ For each file in the podcast feed directory, create a 
            pcast:// link
        """

        links = {}

        # Open the directory and walk through all the xml files:
        for (thisDir, subdirs_found, files_found) in os.walk(podcast_feed_dir):
            for filename in files_found:
                if ".xml" in filename: # Just to be sure we're only grabbing xml files
                    links[filename[:-4]] = 'pcast://{}/podcasts/{}'.format(get_ip(), filename)
                    
        return links
    
    def _create_new_webpage(self, podcast_links):

        # Build the html document
        html_root = ET.Element("html")
        html_head = ET.SubElement(html_root, "head")
        title = ET.SubElement(html_head, "title")
        title.text = "iTunes Podcast Feeds"
        html_body = ET.SubElement(html_root, "body")
        for pod_title, file in podcast_links.items():
            html_p = ET.SubElement(html_body, "p")
            feed_link = ET.SubElement(html_p, "a")
            feed_link.attrib['href'] = file
            feed_link.text = "Subscribe to {} podcast in iTunes".format("pod_title")
            logger.info("Added a subscription link for the podcast: %s", pod_title)

        html_tree = ET.ElementTree(html_root)
        with open(self.webpage_path, "w") as f:
            logger.info("Opened %s to write html", self.webpage_path)
            html_tree.write(f, pretty_print=True)

    def _add_to_webpage(self, podcast_links):

        logger.info("Opening %s for html parsing", self.webpage_path)
        parser = ET.XMLParser(remove_blank_text=True)
        html_tree = ET.parse(self.webpage_path, parser)
        html_root = html_tree.getroot()

        for pod_title, file in podcast_links.items():

            if file not in [link.attrib['href'] for link in html_tree.iterfind('a')]:
                feed_link = ET.SubElement("p", "a")
                feed_link.attrib['href'] = file
                feed_link.text = "Subscribe to {} podcast in iTunes".format(pod_title)
                logger.info("Just added title \"%s\" to the html podcast feeds page", pod_title)

        html_tree = ET.ElementTree(html_root)
        with open(self.webpage_path, "w") as f:
            logger.info("Opened %s to write html", self.webpage_path)
            html_tree.write(f, pretty_print=True)

    def gen_webpage(self, podcast_feed_dir):
        """ Generate & update the webpage for subscription links for 
            iTunes podcasts
        """

        podcast_links = self._create_podcast_links(podcast_feed_dir)

        if not os.path.exists(self.webpage_path):
            self._create_new_webpage(podcast_links)
        else:
            self._add_to_webpage(podcast_links)

class PodcastSubscriptionManager(object):

    def __init__(self, podcast_list, podcast_feed_dir, webpage_path):
        self.podcast_list = podcast_list
        self.podcast_feed_dir = podcast_feed_dir
        self.webpage_path = webpage_path

    def add_new_episodes(self):
        """ This function cycles through the new podcast xml data generated in the
            script and appends it to the xml file with the appropriate tags.
            new_data is the data generated from the show's xml file.
            podcast_list is the appropriate podcast xml file.
        """

        for podcast in self.podcast_list:

            podcast_manager = PodcastSubscriptionFeedManager(podcast.podcast_dir, podcast.podcast_feed_dir)

            if not os.path.isfile(podcast.feed_xml_path):
                podcast_manager.create_new_podcast_feed(podcast.show_data, podcast.feed_xml_path)

            for episode in podcast.episodes:
                podcast_manager.add_to_podcast_feed(episode.episode_data, podcast.feed_xml_path)

        logger.info("Finished adding new podcast episodes")

        logger.info("Now generating the new webpage...")

        webpage = PodcastSubscriptionWebPage(self.webpage_path)
        webpage.gen_webpage(self.podcast_feed_dir)