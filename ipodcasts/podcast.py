# -*- coding: utf-8 -*-

import logging
from lxml import etree as ET
from bs4 import BeautifulSoup
import requests

from ipodcasts import PodcastXML
from ipodcasts.episode import PodcastEpisode

logger = logging.getLogger(__name__)


class PodcastSeriesXML(PodcastXML):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_description(page):
        """ Scrape the BBC website for the show's general description.
            We look for the following tags:
            <div class="map__intro__synopsis centi" property="description">
              <p> -example desc- </p>
            </div>
        """

        iplayer_request = requests.get(page)
        if iplayer_request.status_code == 200:
            iplayer_page = iplayer_request.text
            soup = BeautifulSoup(iplayer_page, "lxml")
            desc = soup.find(property='description')
            description = str(desc.string)
        else:
            logger.warning("Failed to retrieve the iplayer page")
            description = ''

        return description

    def get_podcast_data(self, episode_xml_file):
        """ Take a episode xml file, parse it and extract information
            about the Podcast series and store in the appropriate form
            to be added into an xml file
        """

        # Open the file and get the information out.
        self.xml_tree = episode_xml_file

        podcast_title = self._tag_text("name")
        podcast_web_home = self._tag_text("web")
        description = self._get_description(podcast_web_home)
        thumbnail = self._tag_text("thumbnail")
        # Get the first 4 characters of the first published date which is in the format YYYY-MM-DDTHH:MM:SSz
        cr_year = self._tag_text("firstbcast")[:4]

        new_show = {
            'title': podcast_title,
            'link': podcast_web_home,
            'description': description,
            'summary': description,
            'image': thumbnail,
            'author': self._tag_text("channel"),
            'keywords': self._tag_text("categories"),
            'category': self._tag_text("category"),
            'copyright': "BBC &#169; " + cr_year,
            'owner': {
                'name': podcast_title
            },
            'image_p': {
                'url': thumbnail,
                'title': podcast_title,
                'link': podcast_web_home,
            },
        }

        return new_show


class EpisodeList(list):

    def __init__(self, parent_podcast):
        super().__init__(self)
        self.__parent = parent_podcast

    def append(self, episode):

        if not isinstance(episode, PodcastEpisode):
            raise TypeError("You're attempting to add a non-podcast episode to the podcast episode list")

        if episode.series != self.__parent.series:
            raise ValueError("You're adding an episode that belongs to a different series. Podcast series: %s; episode "
                             "series: %s", (self.__parent.series, episode.series))

        if not self:
            series_xml = PodcastSeriesXML()
            self.__parent.show_data = series_xml.get_podcast_data(episode.xml_path)

        super(EpisodeList, self).append(episode)


class Podcast(object):
    """ Object to represent a particular podcast series """

    def __init__(self, series, feed_xml_path):
        self._series = series
        self._feed_xml_path = feed_xml_path
        self._show_data = None
        self.episodes = EpisodeList(self)
        
    @property
    def series(self):
        return self._series
    
    @series.setter
    def series(self, series):
        if not self._series:
            self._series = series

    @property
    def feed_xml_path(self):
        return self._feed_xml_path

    @feed_xml_path.setter
    def feed_xml_path(self, feed_xml_path):
        if not self._feed_xml_path:
            self._feed_xml_path = feed_xml_path

    @property
    def show_data(self):
        return self._show_data

    @show_data.setter
    def show_data(self, podcast_data):
        if not self._show_data:
            self._show_data = podcast_data
