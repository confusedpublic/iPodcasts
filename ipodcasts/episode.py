# -*- coding: utf-8 -*-

import os
import re
import datetime
import logging
from subprocess import Popen, PIPE

from ipodcasts import get_ip, PodcastXML


logger = logging.getLogger(__name__)


class PodcastEpisodeXML(PodcastXML):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _tidy_episode_title(episode_title):
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

        episode_re = re.compile(r'^([0-9])\..*(\1)')
        episode_match = episode_re.search(episode_title)

        if episode_match:
            episode_title = re.sub(r'^[0-9]\.(\s+)?', '', episode_title)

        return episode_title

    @staticmethod
    def _format_published_time(timestring):
        """ This function formats the first published date from the get_iplayer xml
            file, which is in the ISO8601 format (set in the get_iplayer preferences).
            This format includes a UTC offset at the end, which can be inconvenient,
            as there doesn't seem to be any good way of handling the off sets.

            The function splits the time into a list for each character, then combines
            the first 18 figures to produce the time and the last 1 to 6 figures to
            produce the off set (it's either Z or +00:00).

            e.g. 2015-11-26T04:00:00Z is split into a list: (2, 0, 1, 5 ...)
            The first 19 characters form the time (2015-11-26T04:00:00), and the last
            character (Z) forms the off set.

        :param timestring str:
        :return: str
        """

        logger.debug("Received %s"), timestring

        timestring = timestring.replace("Z", "+00:00")
        timestring = ''.join(timestring.rsplit(':', 1))

        parsed_time = datetime.datetime.strptime(timestring, '%Y-%m-%dT%H:%M:%S%z')
        published_time = datetime.datetime.strftime(parsed_time, "%a, %d %b %Y %H:%M:%S GMT")

        return published_time

    def get_episode_data(self, episode_xml_file, file_name, duration, duration_datetime):
        """
            The enclosure tag will have attributes rather than text values, so we'll put the in an embedded dictionary.
            get_iplayer's output xml file doesn't seem to have an explicit tag, so we'll set it as no by default
        :return:
        """

        self.xml_tree = episode_xml_file

        file_http_address = 'http://{}/radio_podcasts/{}'.format(get_ip(), file_name)
        short_description = self._tag_text("descshort")

        feed_xml = {
            'enclosure': {
                'type': "audio/mpeg",
                'url': file_http_address,
                'duration': duration,
            },
            'duration': duration_datetime,
            'explicit': "no",
            'title': self._tidy_episode_title(self._tag_text("episode")),
            'description': self._tag_text("desclong"),
            'subtitle': short_description,
            'summary': short_description,
            'pubDate': self._format_published_time(self._tag_text("firstbcast")),
            'author': self._tag_text("channel"),
            'keywords': self._tag_text("categories"),
        }

        return feed_xml


class PodcastEpisode(object):
    """ Object to represent an episode of a particular podcast series
    """

    def __init__(self):
        self._title = ""
        self._series = ""
        self._season_number = 0
        self._episode_number = 0
        self._file_path = ""
        self._xml_path = ""
        self._duration = 0
        self._duration_datetime = None
        self._episode_data = None

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, pod_title):
        if not self._title:
            self._title = pod_title

    @property
    def episode_number(self):
        return self._episode_number

    @property
    def series(self):
        return self._series

    @series.setter
    def series(self, pod_series):
        if not self._series:
            self._series = pod_series

    @property
    def season_number(self):
        return self._season_number
            
    @season_number.setter
    def season_number(self, pod_season_number):
        if not self._season_number:
            if isinstance(pod_season_number, (bytes, str)):
                if pod_season_number[0] == '0':
                    pod_season_number = pod_season_number[1]
                pod_season_number = int(pod_season_number)
            elif not isinstance(pod_season_number, int):
                raise ValueError("The season number must an integer or (zero padded) string")
            self._season_number = pod_season_number

    @episode_number.setter
    def episode_number(self, pod_episode_number):
        if not self._episode_number:
            if isinstance(pod_episode_number, (bytes, str)):
                if pod_episode_number[0] == '0':
                    pod_episode_number = pod_episode_number[1]
                pod_episode_number = int(pod_episode_number)
            elif not isinstance(pod_episode_number, int):
                raise ValueError("The episode number must an integer or (zero padded) string")
            self._episode_number = pod_episode_number

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, pod_file_path):
        if not self._file_path:
            if not os.path.exists(pod_file_path):
                raise FileNotFoundError("Supplied podcast file does not exist here")
            _, pod_extension = os.path.splitext(pod_file_path)
            if not pod_extension == '.mp3':
                raise TypeError("Supplied podcast file is not an mp3, but a %s", pod_extension)
            self._file_path = pod_file_path
        self.duration = pod_file_path

    @property
    def xml_path(self):
        return self._xml_path

    @xml_path.setter
    def xml_path(self, pod_xml_path):
        if not self._xml_path:
            if not os.path.exists(pod_xml_path):
                raise FileNotFoundError("Supplied podcast xml file does not exist at %s" % pod_xml_path)
            _, pod_xml_extension = os.path.splitext(pod_xml_path)
            if not pod_xml_extension == '.xml':
                raise TypeError("Supplied podcast xml file is not an xml, but a %s", pod_xml_extension)
            self._xml_path = pod_xml_path

    @property
    def duration_datetime(self):
        return self._duration_datetime

    @duration_datetime.setter
    def duration_datetime(self, durationdatetime):
        if not self._duration_datetime:
            self.duration_datetime = durationdatetime

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, file_path):
        """ Unfortunately get_iplayer does not report a correct length for the
            podcasts. To fix this we need to look at the actual file. An easy way of
            doing this is to use the ffmpeg -i (info) shell command (as we use ffmpeg
            with get_iplayer anyway. We simply run the command, awk the output for
            the duration (which contains a trialing ',', which we can trim off) and
            return the length in seconds from the function.

            While this is simple enough to *do*, it was a bit of a nightmare to get
            *working*. Basically, in order to use pipes and awk the output of the
            ffmpeg command, you have to have the shell=True option. This also lets
            the command be a string. Otherwise you have to run the command as a
            list, where each command, flag, argument, etc. is a different item in
            the list.
            Also, because we're running the subprocess.check_output function as
            shell=True, we get a '\n' on the end of our string, so we have to cut that
            off as well.
        """
        if not self._duration:
            length_shell_command = ["ffmpeg", "-i", file_path]
            run_length_cmd = Popen(length_shell_command, stdout=PIPE, stderr=PIPE)
            stdout, stderr = run_length_cmd.communicate()
            # TODO: Check that the user running the script can access the ffmpeg command.

            duration_regex = re.compile(r'Duration: (?P<hour>[0-9]{2}):(?P<min>[0-9]{2}):(?P<sec>[0-9]{2})\.[0-9]{2}')
            output_lines = stderr.split('\n')
            [duration_match] = [duration_regex.search(line) for line in output_lines]
            d_hour = duration_match.group('hour')
            d_min = duration_match.group('min')
            d_sec = duration_match.group('sec')
            self._duration_datetime = "{}:{}:{}".format(d_hour, d_min, d_sec)
            podcast_length = datetime.timedelta(hours=d_hour, minutes=d_min, seconds=d_sec).total_seconds()
            # Cut the trailing .0 off the total_seconds
            podcast_length = str(podcast_length)[:-2]

            self.duration = podcast_length

    @property
    def episode_data(self):
        if not self._episode_data:
            episode_xml = PodcastEpisodeXML()
            return episode_xml.get_episode_data(self.xml_path, self.file_path, self.duration, self.duration_datetime)
