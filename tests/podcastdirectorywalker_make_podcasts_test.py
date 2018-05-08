# -*- coding: utf-8 -*-

import mock
import logging
import os

from ipodcasts import Podcast
from ipodcasts.scan_for_xml import PodcastDirectoryWalker


logging.basicConfig(level=logging.DEBUG)


class TestPDWMakePodcasts(object):

    def test_empty_directory(self, tmpdir):

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert list(pdw.make_podcasts()) == []

    @mock.patch('os.walk')
    def test_empty_subdirectory(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        mock_walk.return_value = [
            (tmpdir, (foo, ), (),),
            (foo, (), ())
        ]

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert list(pdw.make_podcasts()) == []

    @mock.patch('os.walk')
    def test_single_mp3(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_pod = foo.join('thepod.S01E01.first.mp3')
        first_pod.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_pod), ))
        ]

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert list(pdw.make_podcasts()) == []

    @mock.patch('os.walk')
    def test_single_mp3_bad_name(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_pod = foo.join('first.mp3')
        first_pod.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_pod), ))
        ]

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert list(pdw.make_podcasts()) == []

    @mock.patch('os.walk')
    def test_correct_podcast(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('thepod.S01E01.title.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('thepod.S01E01.title.xml')
        first_xml.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            )
             )
        ]

        expected_podcast = Podcast()
        expected_podcast.title = 'title'
        expected_podcast.file_path = str(first_mp3)
        expected_podcast.xml_path = str(first_xml)
        expected_podcast.series = 'thepod'
        expected_podcast.season_number = '01'
        expected_podcast.episode_number = '02'

        pdw = PodcastDirectoryWalker(tmpdir)
        pdw._podcast_walk()

        result_podcast = next(pdw.make_podcasts())

        assert result_podcast == expected_podcast

    @mock.patch('os.walk')
    def test_ignore(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('S01E01.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('S01E01.xml')
        first_xml.write('tester')
        first_ignore = foo.join('S01E01.ignore')
        first_ignore.write('test')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            os.path.basename(first_ignore)))
        ]

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert pdw.ignored_podcasts == ['S01E01']
        assert pdw.podcast_files == {}

    @mock.patch('os.walk')
    def test_partial(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('S01E01.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('S01E01.xml')
        first_xml.write('tester')
        first_partial = foo.join('S01E01.partial')
        first_partial.write('test')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            os.path.basename(first_partial)))
        ]

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert pdw.ignored_podcasts == ['S01E01']
        assert pdw.podcast_files == {}

    @mock.patch('os.walk')
    def test_two_correct_podcast(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('thepod.S01E01.title.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('thepod.S01E01.title.xml')
        first_xml.write('tester')
        second_mp3 = foo.join('thepod.S01E02.title2.mp3')
        second_mp3.write('tester')
        second_xml = foo.join('thepod.S01E02.title2.xml')
        second_xml.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            os.path.basename(second_mp3),
                            os.path.basename(second_xml),
                            ))
        ]

        expected_podcasts = {
            'thepod.S01E01.title': {
                'title': 'title',
                'path': str(first_mp3),
                'file_types': ['.mp3', '.xml'],
                'series': 'thepod',
                'season_number': '01',
                'ep_number': '01',
            },
            'thepod.S01E02.title2': {
                'title': 'title2',
                'path': str(second_mp3),
                'file_types': ['.mp3', '.xml'],
                'series': 'thepod',
                'season_number': '01',
                'ep_number': '02',
            }
        }

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert pdw.ignored_podcasts == []
        assert pdw.podcast_files == expected_podcasts

    @mock.patch('os.walk')
    def test_one_correct_one_ignore_podcast(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('thepod.S01E01.title.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('thepod.S01E01.title.xml')
        first_xml.write('tester')
        second_mp3 = foo.join('thepod.S01E02.title.mp3')
        second_mp3.write('tester')
        second_xml = foo.join('thepod.S01E02.title.xml')
        second_xml.write('tester')
        second_ignore = foo.join('thepod.S01E02.title.ignore')
        second_ignore.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            os.path.basename(second_mp3),
                            os.path.basename(second_xml),
                            os.path.basename(second_ignore),
                            ))
        ]

        expected_podcasts = {
            'thepod.S01E01.title': {
                'title': 'title',
                'path': first_mp3,
                'file_types': ['.mp3', '.xml'],
                'series': 'thepod',
                'season_number': '01',
                'ep_number': '01',
            }
        }

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert pdw.ignored_podcasts == ['thepod.S01E02.title']
        assert pdw.podcast_files == expected_podcasts

    @mock.patch('os.walk')
    def test_one_correct_one_partial_podcast(self, mock_walk, tmpdir):

        foo = tmpdir.mkdir('foo')
        first_mp3 = foo.join('thepod.S01E01.title.mp3')
        first_mp3.write('tester')
        first_xml = foo.join('thepod.S01E01.title.xml')
        first_xml.write('tester')
        second_mp3 = foo.join('thepod.S01E02.title.mp3')
        second_mp3.write('tester')
        second_xml = foo.join('thepod.S01E02.title.xml')
        second_xml.write('tester')
        second_partial = foo.join('thepod.S01E02.title.partial')
        second_partial.write('tester')

        mock_walk.return_value = [
            (str(tmpdir), (str(foo), ), (),),
            (str(foo), (), (os.path.basename(first_mp3),
                            os.path.basename(first_xml),
                            os.path.basename(second_mp3),
                            os.path.basename(second_xml),
                            os.path.basename(second_partial),
                            ))
        ]

        expected_podcasts = {
            'thepod.S01E01.title': {
                'title': 'title',
                'path': first_mp3,
                'file_types': ['.mp3', '.xml'],
                'series': 'thepod',
                'season_number': '01',
                'ep_number': '01',
            }
        }

        pdw = PodcastDirectoryWalker(tmpdir)

        pdw._podcast_walk()

        assert pdw.ignored_podcasts == ['thepod.S01E02.title']
        assert pdw.podcast_files == expected_podcasts



