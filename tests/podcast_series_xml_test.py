# -*- coding: utf-8 -*-

import mock
import pytest
from lxml import etree

from ipodcasts.episode import PodcastEpisodeXML


class TestPodcastEpisodeXML(object):

    ep_title_ids = [
        'no_name',
        'no_numbers',
        'number_at_end',
        'number_dot_name_number',
        'number_dot_space_name_number',
        'different_numbers'
    ]

    @pytest.mark.parametrize('episode_name, expected', (
            ('', ''),
            ('Episode', 'Episode'),
            ('Episode 3', 'Episode 3'),
            ('3.Episode 3', 'Episode 3'),
            ('3. Episode 3', 'Episode 3'),
            ('3. Episode 4', '3. Episode 4')
    ), ids=ep_title_ids)
    def test_tidy_episode_title(self, episode_name, expected):

        e_xml = PodcastEpisodeXML()
        result = e_xml._tidy_episode_title(episode_name)

        assert expected == result

    def test_format_published_string_no_string(self):

        with pytest.raises(ValueError):
            PodcastEpisodeXML._format_published_time('')

    published_string_ids = [
        'normal_string_ends_with_z',
        'normal_string_ends_with_hours'
    ]

    @pytest.mark.parametrize('test_string, expected', (
        ('2015-11-26T04:00:00Z', 'Thu, 26 Nov 2015 04:00:00 GMT'),
        ('2015-11-26T04:00:00+00:00', 'Thu, 26 Nov 2015 04:00:00 GMT'),
    ), ids=published_string_ids)
    def test_format_published_string(self, test_string, expected):

        result = PodcastEpisodeXML._format_published_time(test_string)

        assert expected == result

    @mock.patch('ipodcasts.episode.get_ip')
    # @mock.patch('ipodcasts.episode.PodcastEpisodeXML.xml_tree')
    def test_get_episode_data(self, mock_get_ip, tmpdir):

        test_xml = (
            '<?xml version="1.0" ?>\n'
            '<program_meta_data xmlns="eg_namespace" revision="1">\n\t'
            '<brand>Radio 1\'s Essential Mix</brand>\n\t'
            '<descshort>Short Description</descshort>\n\t'
            '<desclong>Much longer description about the Podcast Episode</desclong>\n\t'
            '<episode>Episode 3</episode>\n\t'
            '<firstbcast>2015-11-26T04:00:00+00:00</firstbcast>\n\t'
            '<channel>BBC Radio 1</channel>\n\t'
            '<categories>Music, Dance, Electronica</categories>\n'
            '</program_meta_data>'
            )
        test_xml_file = tmpdir.join('podcast.xml')
        test_xml_file.write(test_xml)

        mock_get_ip.return_value = '127.0.0.1'

        expected = {
            'enclosure': {
                'type': "audio/mpeg",
                'url': "http://127.0.0.1/radio_podcasts/podcasts.S01E01.title",
                'duration': "100",
            },
            'duration': "01:20:00",
            'explicit': "no",
            'title': "Episode 3",
            'description': "Much longer description about the Podcast Episode",
            'subtitle': "Short Description",
            'summary': "Short Description",
            'pubDate': "Thu, 26 Nov 2015 04:00:00 GMT",
            'author': "BBC Radio 1",
            'keywords': "Music, Dance, Electronica",
        }

        pe_xml = PodcastEpisodeXML(get_iplayer_ns_string="eg_namespace")
        print(pe_xml.xml_tree)

        result = pe_xml.get_episode_data(str(test_xml_file), "podcasts.S01E01.title", "100", "01:20:00")

        assert expected == result
