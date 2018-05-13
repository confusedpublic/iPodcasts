# -*- coding: utf-8 -*-

import mock
import pytest

from ipodcasts.podcast import Podcast, EpisodeList
from ipodcasts.episode import PodcastEpisode

MOCK_PODCAST = mock.MagicMock(spec=Podcast)
MOCK_PODCAST.series = "series"
MOCK_PODCAST.feed_xml_path = "/tmp/podcast.xml"


class TestEpisodeList(object):

    def test_constructor(self):

        el = EpisodeList(MOCK_PODCAST)

        assert MOCK_PODCAST == el.__dict__['_EpisodeList__parent']

    def test_append_wrong_type(self):

        el = EpisodeList(MOCK_PODCAST)

        with pytest.raises(TypeError):
            el.append('a')

    def test_append_wrong_series(self):

        el = EpisodeList(MOCK_PODCAST)
        e = mock.MagicMock(spec=PodcastEpisode)
        e.series = "wrong_series"

        with pytest.raises(ValueError):
            el.append(e)

    @mock.patch('ipodcasts.podcast.PodcastSeriesXML.get_podcast_data')
    def test_append_to_empty_self(self, mock_podcast_data):

        mock_podcast_data.return_value = {'mock': 'data'}

        el = EpisodeList(MOCK_PODCAST)
        e = mock.MagicMock(spec=PodcastEpisode)
        e.series = "series"

        el.append(e)

        assert 1 == len(el)

    @mock.patch('ipodcasts.podcast.PodcastSeriesXML.get_podcast_data')
    def test_append_multiple_episodes(self, mock_podcast_data):

        mock_podcast_data.return_value = {'mock': 'data'}

        el = EpisodeList(MOCK_PODCAST)
        e = mock.MagicMock(spec=PodcastEpisode)
        e.series = "series"
        f = mock.MagicMock(spec=PodcastEpisode)
        f.series = "series"

        el.append(e)

        assert 1 == len(el)

        el.append(f)

        assert 2 == len(el)
        assert 1 == mock_podcast_data.call_count
