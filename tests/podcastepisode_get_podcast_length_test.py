# -*- coding: utf-8 -*-

import pytest


from ipodcasts.episode import PodcastEpisode


class TestGetPodcastLength(object):

    def test_no_file(self):
        pass
        #
        # with pytest.raises(ValueError):
        #     PodcastEpisode().duration = ""

    # ids = [
    #     'normal_string_ends_with_z',
    #     'normal_string_ends_with_hours'
    # ]
    #
    # @pytest.mark.parametrize('test_string, expected', (
    #     ('2015-11-26T04:00:00Z', 'Thu, 26 Nov 2015 04:00:00 GMT'),
    #     ('2015-11-26T04:00:00+00:00', 'Thu, 26 Nov 2015 04:00:00 GMT'),
    # ), ids=ids)

    #
    # def test_get_podcast_duration(self, test_string, expected):
    #
    #     result = get_podcast_duration(test_string)
    #
    #     assert expected == result
