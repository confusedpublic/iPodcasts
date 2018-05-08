# -*- coding: utf-8 -*-

import pytest
import logging

from ipodcasts.scan_for_xml import PodcastDirectoryWalker


logging.basicConfig(level=logging.DEBUG)


class TestPDWProcessFilename(object):

    numbers_ids = [
        'no_filename',
        'no_series',
        'no_episode',
        'properly_formed',
        'two_episodes',
        'three_digit_series',
        'three_digit_episode',
        'dot_separator_everything'
    ]

    names_ids = numbers_ids + [
        'no_pod_name',
        'upper',
        'with_digit',
        'include_single_dot_in_title',
        'include_single_dot_in_title_and_numbers',
        'include_two_dots'
    ]

    title_ids = names_ids + [
        'no_title',
        'multiple_words'
    ]

    @pytest.mark.parametrize("test_filename, expected", [
        ("", (None, None)),
        ("E01_prod", (None, None)),
        ("S01_pod", (None, None)),
        ("thepod.S01E01.title", ("01", "01")),
        ("thepod.SS01E21E22.title", ("00", "00")),  # TODO: Do double episodes occur?
        ("thepod.S500E01.title", ("500", "01")),
        ("thepod.S01E500.title", ("01", "500")),
        ("thepod.S01.E01.title", (None, None)),
    ], ids=numbers_ids)
    def test_get_numbers(self, test_filename, expected):

        _, result_season, result_episode, _ = PodcastDirectoryWalker._process_filename(test_filename)

        assert expected == (result_season, result_episode)

    @pytest.mark.parametrize("test_filename, expected", [
        ("", None),
        ("thepod.E01_prod", "thepod"),
        ("thepod.S01_pod", "thepod"),
        ("thepod.S01E01.title", "thepod"),
        ("thepod.SS01E21E22.title", "thepod"),
        ("thepod.S500E01.title", "thepod"),
        ("thepod.S01E500.title", "thepod"),
        ("thepod.S01.E01.title", None),
        ("S01E01.title", None),
        ("THEPOD.S01E01.title", "THEPOD"),
        ("th3p0d.S01E01.title", "th3p0d"),
        ("the.pod.title", "the.pod"),
        ("the.pod.S01E01.title", None),
        ("the.p.od.S01E01.title", None),
    ], ids=names_ids)
    def test_get_name(self, test_filename, expected):
        result_name, _, _, _ = PodcastDirectoryWalker._process_filename(test_filename)

        assert expected == result_name

    @pytest.mark.parametrize("test_filename, expected", [
        ("", None),
        ("thepod.E01.title", "title"),
        ("thepod.S01.title", "title"),
        ("thepod.S01E01.title", "title"),
        ("thepod.SS01E21E22.title", "title"),
        ("thepod.S500E01.title", "title"),
        ("thepod.S01E500.title", "title"),
        ("thepod.S01.E01.title", None),
        ("S01E01.title", None),
        ("thepod.S01E01.TITLE", "TITLE"),
        ("thepod.S01E01.T1TL3", "T1TL3"),
        ("the.pod.title", "title"),
        ("the.pod.S01E01.title", None),
        ("the.p.od.S01E01.title", None),
        ("the.pod.S01E01", None),
        ("thepod.S01E01.title_with_many_words", "title_with_many_words"),
    ], ids=title_ids)
    def test_get_title(self, test_filename, expected):
        _, _, _, result_title = PodcastDirectoryWalker._process_filename(test_filename)

        assert expected == result_title

    all_parts_ids = [
        'no_filename',
        'properly_formed',
        'two_episode_numbers',
        'three_digit_season_number',
        'three_digit_episode_number',
        'dot_separator',
        'dot_in_title_no_numbers',
        'long_title'
    ]

    @pytest.mark.parametrize("test_filename, expected", [
        ("", (None, None, None, None)),
        ("thepod.S01E01.title", ("thepod", "01", "01", "title")),
        ("thepod.SS01E21E22.title", "title"),
        ("thepod.S500E01.title", ("thepod", "500", "01", "title")),
        ("thepod.S01E500.title", ("thepod", "01", "500", "title")),
        ("thepod.S01.E01.title", (None, None, None, None)),
        ("the.pod.title", ("the.pod", "00", "00", "title")),
        ("thepod.S01E01.title_with_many_words", ("thepod", "01", "01", "title_with_many_words")),
    ], ids=all_parts_ids)
    def test_all_parts(self, test_filename, expected):
        result = PodcastDirectoryWalker._process_filename(test_filename)

        assert expected == result
