# -*- coding: utf-8 -*-

import mock
import pytest

from ipodcasts.episode import PodcastEpisode


class TestPocastEpisodeProperties(object):

    def test_title(self):

        p = PodcastEpisode()
        p.title = "pod title"

        assert p.title == "pod title"

    def test_title_doesnt_change(self):

        p = PodcastEpisode()
        p.title = "pod title"
        p.title = "some other title"

        assert p.title == "pod title"

    def test_season_number_int(self):

        p = PodcastEpisode()
        p.season_number = 10

        assert p.season_number == 10

    def test_season_number_str(self):

        p = PodcastEpisode()

        p.season_number = str("10")

        assert p.season_number == 10

    def test_season_number_bytes_zero_padded(self):

        p = PodcastEpisode()

        p.season_number = "01"

        assert p.season_number == 1

    def test_season_number_wrong_type(self):

        p = PodcastEpisode()

        with pytest.raises(ValueError):
            p.season_number = float(10)

    def test_episode_number_int(self):

        p = PodcastEpisode()
        p.episode_number = 10

        assert p.episode_number == 10

    def test_episode_number_str(self):

        p = PodcastEpisode()

        p.episode_number = str("10")

        assert p.episode_number == 10

    def test_episode_number_bytes_zero_padded(self):

        p = PodcastEpisode()

        p.episode_number = "01"

        assert p.episode_number == 1

    def test_episode_number_wrong_type(self):

        p = PodcastEpisode()

        with pytest.raises(ValueError):
            p.episode_number = float(10)

    def test_series(self):

        p = PodcastEpisode()
        p.series = "pod series"

        assert p.series == "pod series"

    @mock.patch('ipodcasts.episode.PodcastEpisode.duration')
    def test_file_path(self, mock_duration, tmpdir):

        mock_duration.return_value = "00:00:00"

        # create tmp mp3 file
        pod = tmpdir.join("podcast.mp3")
        pod.write('test podcast')

        p = PodcastEpisode()
        p.file_path = pod
        assert p.file_path == str(pod)

    def test_file_path_not_mp3(self, tmpdir):

        # create tmp mp3 file
        pod = tmpdir.join("podcast.xml")
        pod.write('test podcast')

        p = PodcastEpisode()

        with pytest.raises(TypeError):
            p.file_path = pod

    def test_file_path_doesnt_exist(self, tmpdir):

        # create tmp mp3 file
        pod = tmpdir.join("podcast.mp3")

        p = PodcastEpisode()

        with pytest.raises(FileNotFoundError):
            p.file_path = pod

    def test_xml_path(self, tmpdir):

        # create tmp xml file
        pod = tmpdir.join("podcast.xml")
        pod.write('test podcast xml')

        p = PodcastEpisode()
        p.xml_path = pod
        assert p.xml_path == str(pod)

    def test_xml_path_not_xml(self, tmpdir):

        # create tmp xml file
        pod = tmpdir.join("podcast.mp3")
        pod.write('test podcast')

        p = PodcastEpisode()

        with pytest.raises(TypeError):
            p.xml_path = pod

    def test_xml_path_doesnt_exist(self, tmpdir):

        # create tmp xml file
        pod = tmpdir.join("podcast.xml")

        p = PodcastEpisode()

        with pytest.raises(FileNotFoundError):
            p.xml_path = pod

