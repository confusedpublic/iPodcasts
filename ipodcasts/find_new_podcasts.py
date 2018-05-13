# -*- coding: utf-8 -*-
"""
This is another simple script which is called if do_scan is returned
true. This scans the relevant podcast directory (found in the config
file) for new xml files. If it finds them, it adds them to a dictionary
and creates a .ignore file with the same prefix so that we don't add a
podcast twice. (It also checks for the .ignore file before adding the
xml file to the dictionary of course. I chose this method over keeping
track of the files in an db as the .ignore files can be cleaned out
more easily with the original files
"""


import os
import logging
import re

from ipodcasts.podcast import Podcast
from ipodcasts.episode import PodcastEpisode


# Set the log
logger = logging.getLogger( __name__)


class PodcastDirectoryWalker(object):
    """ Podcast directory structure:
            /mnt/Ridcully/Media/Radio/
            /mnt/Ridcully/Media/Radio/The_News_Quiz
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_92
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_88
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_90
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_89
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_91
            /mnt/Ridcully/Media/Radio/The_News_Quiz/Season_
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra/Season_16
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra/Season_18
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra/Season_15
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra/Season_17
            /mnt/Ridcully/Media/Radio/News_Quiz_Extra/Season_19
            /mnt/Ridcully/Media/Radio/B.Traits
            /mnt/Ridcully/Media/Radio/Friction
            /mnt/Ridcully/Media/Radio/BBC_Radio_1s_Essential_Mix
            /mnt/Ridcully/Media/Radio/BBC_Radio_1s_Residency
            /mnt/Ridcully/Media/Radio/Terry_Pratchett
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Only_You_Can_Save_Mankind
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Guards_Guards
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Night_Watch
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Eric
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Wyrd_Sisters
            /mnt/Ridcully/Media/Radio/Terry_Pratchett/Small_Gods
    """

    def __init__(self, directory, file_suffixes=None):
        self.directory = os.path.abspath(directory)
        self.file_suffixes = ['.mp3', '.xml', '.jpg', '.ignore'] if not file_suffixes else file_suffixes
        self.ignored_podcasts = []
        self.podcast_files = {}

    @staticmethod
    def _are_ignoring(file_name, file_types):
        """ Check if we're ignoring this file """

        if not file_name or not file_types:
            logger.warning("Didn't pass a filename or file types, ignoring. Entered data: "
                           "filename: %s; file types: %s" % (file_name, file_types))
            return True

        explicitly_ignoring = '.ignore' in file_types
        has_xml_no_mp3 = '.xml' in file_types and '.mp3' not in file_types
        has_mp3_no_xml = '.mp3' in file_types and '.xml' not in file_types

        if ".partial" in file_types:
            ignore_partial = True
            logger.debug("Partially downloaded file, don't want yet")
        else:
            ignore_partial = False

        if explicitly_ignoring:
            logger.debug("Explicitly ignoring this file, has an .ignore file")

        if has_xml_no_mp3:
            logger.warning("The .xml file %s.xml exists but the .mp3 file does not", file_name)
        if has_mp3_no_xml:
            logger.warning("The .mp3 file %s.mp3 exists but the .xml file does not", file_name)

        return explicitly_ignoring or has_xml_no_mp3 or has_mp3_no_xml or ignore_partial

    @staticmethod
    def _process_filename(filename):
        """ Use regex to process the filename to obtain the podcast
            name, series and episode numbers (if present) and podcast
            title
            Example names:
                The_News_Quiz.s88e08.8._Episode_8
                B.Traits.Ibiza_Special
        """

        podcast_numbers_match = re.compile(
            r'^(?P<pod_name>[a-zA-Z0-9_]+)\.S(?P<season>[0-9]{2,3})E(?P<episode>[0-9]{2,3})\.'
            r'(?P<title>[a-zA-Z0-9_]+)$')
        podcast_match = re.compile(r'^(?P<pod_name>[a-zA-Z_]+(\.[a-zA-Z0-9]+?)?)'
                                   r'(\.(?P<title>(?!S[0-9]{2}E[0-9]{2})[a-zA-Z0-9_]+))$')

        episode_details_numbers = podcast_numbers_match.search(filename)
        episode_details = podcast_match.search(filename)
        if episode_details_numbers:
            logger.debug("matched with season/episode details")
            name = episode_details_numbers.group('pod_name')
            season = episode_details_numbers.group('season')
            episode = episode_details_numbers.group('episode')
            title = episode_details_numbers.group('title')
        elif episode_details:
            logger.debug("matched with just name/title details")
            name = episode_details.group('pod_name')
            season = '00'
            episode = '00'
            title = episode_details.group('title')
        else:
            logger.warning("%s has a poorly formed name, won't be processing", filename)
            name = season = episode = title = None

        return name, season, episode, title

    def _podcast_walk(self):
        """ Walks the podcast dir
        :return:
        """

        podcast_files = {}
        ignored = []

        for this_dir, subdirs_found, files_found in os.walk(self.directory):
            logger.debug("%s %s %s" % (this_dir, subdirs_found, files_found))
            for filename in files_found:

                file_name, ext = os.path.splitext(filename)
                name, season_num, ep_num, title = self._process_filename(file_name)

                logger.debug(file_name)
                logger.debug(ext)

                if file_name not in podcast_files:
                    podcast_files[file_name] = {
                        'file_types': [],
                    }
                podcast_files[file_name]['file_types'].append(ext)
                podcast_files[file_name]['title'] = title
                podcast_files[file_name]['path'] = os.path.join(os.path.abspath(this_dir),
                                                                '{}.mp3'.format(file_name),
                                                                )
                podcast_files[file_name]['series'] = name
                podcast_files[file_name]['season_number'] = season_num
                podcast_files[file_name]['ep_number'] = ep_num

        for podcast_file, file_info in podcast_files.items():

            if self._are_ignoring(podcast_file, file_info['file_types']):
                logger.info("Adding %s to the list of ignored podcasts" % podcast_files)
                ignored.append(podcast_file)

        for ignored_podcast in ignored:
            logger.debug("Deleting %s from the wanted podcasts" % ignored_podcast)
            del podcast_files[ignored_podcast]

        logger.debug(podcast_files)

        self.ignored_podcasts = ignored
        self.podcast_files = podcast_files

    def make_podcasts(self):

        self._podcast_walk()

        for p_file, info in self.podcast_files.items():

            new_podcast = PodcastEpisode()
            new_podcast.title = info['title']
            new_podcast.file_path = info['path']
            new_podcast.xml_path = info['path'].replace('.mp3', '.xml')
            new_podcast.series = info['series']
            new_podcast.season_number = info['season_number']
            new_podcast.episode_number = info['ep_number']

            yield new_podcast

    def get_podcasts(self):
        """ Sort podcast episodes into Podcast objects """

        podcast_list = []
        feed_xml_path = ''  # FIXME: Actually make this variable!

        for podcast_episode in self.make_podcasts():

            if not any(episode.series == podcast_episode.series for episode in podcast_list):
                # Not made a podcast for this yet
                podcast = Podcast(podcast_episode.series, feed_xml_path)
            else:
                [podcast] = [pod for pod in podcast_list if pod.series == podcast_episode.series]

            podcast.episodes.append(podcast_episode)

        return podcast_list