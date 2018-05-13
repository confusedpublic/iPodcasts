# -*- coding: utf-8 -*-

import mock

from ipodcasts.podcast import Podcast
from ipodcasts.episode import PodcastEpisode


class TestPocastEpisodeProperties(object):

    def test_constructor(self):

        test_series = "pod_series"
        test_xml_path = "/tmp/podcast.xml"
        p = Podcast(test_series, test_xml_path)

        assert "pod_series" == p.series
        assert "/tmp/podcast.xml" == p.feed_xml_path
        assert None is p.show_data
        assert [] == p.episodes

    def test_series_doesnt_change(self):

        test_series = "pod_series"
        test_xml_path = "/tmp/podcast.xml"
        p = Podcast(test_series, test_xml_path)

        assert "pod_series" == p.series

        p.series = "some other series"

        assert p.series == "pod_series"

    @mock.patch('ipodcasts.podcast.PodcastSeriesXML.get_podcast_data')
    def test_add_episode(self, mock_podcast_data):

        mock_podcast_data.return_value = {'mock': 'data'}

        test_series = "series"
        test_xml_path = "/tmp/podcast.xml"
        e = mock.MagicMock(spec=PodcastEpisode)
        e.series = "series"

        p = Podcast(test_series, test_xml_path)
        p.episodes.append(e)

        assert 1 == len(p.episodes)
        assert {'mock': 'data'} == p.show_data

    @mock.patch('ipodcasts.podcast.PodcastSeriesXML.get_podcast_data')
    def test_add_multiple_episodes(self, mock_podcast_data):

        mock_podcast_data.return_value = {'mock': 'data'}

        test_series = "series"
        test_xml_path = "/tmp/podcast.xml"
        e = mock.MagicMock(spec=PodcastEpisode)
        e.series = "series"
        f = mock.MagicMock(spec=PodcastEpisode)
        f.series = "series"

        p = Podcast(test_series, test_xml_path)
        p.episodes.append(e)

        assert 1 == len(p.episodes)
        assert {'mock': 'data'} == p.show_data

        p.episodes.append(f)

        assert 2 == len(p.episodes)
        assert {'mock': 'data'} == p.show_data
        assert 1 == mock_podcast_data.call_count
