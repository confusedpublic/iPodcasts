# -*- coding: utf-8 -*-

import os


class Podcast(object):
    """ Object to represent the podcast in the code """

    def __init__(self):
        self._title = ""
        self._series = ""
        self._season_number = 0
        self._episode_number = 0
        self._file_path = ""
        self._xml_path = ""

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

    @property
    def xml_path(self):
        return self._xml_path

    @xml_path.setter
    def xml_path(self, pod_xml_path):
        if not self._xml_path:
            if not os.path.exists(pod_xml_path):
                raise FileNotFoundError("Supplied podcast xml file does not exist at %s", pod_xml_path)
            _, pod_xml_extension = os.path.splitext(pod_xml_path)
            if not pod_xml_extension == '.xml':
                raise TypeError("Supplied podcast xml file is not an xml, but a %s", pod_xml_extension)
            self._xml_path = pod_xml_path
