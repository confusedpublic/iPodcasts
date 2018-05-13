# -*- coding: utf-8 -*-

import pytest

from ipodcasts.find_new_podcasts import PodcastDirectoryWalker


class TestPDWAreIgnoring(object):

    ids = [
        'no_filename_no_filetypes',
        'no_filename',
        'no_filetypes',
        'filename_mp3_only',
        'filename_xml_only',
        'explicit_ignore',
        'partial',
        'not_ignored',
        'not_ignored_other_files',
        'mp3_xml_ignore',
        'xml_ignore',
        'mp3_ignore',
        'mp3_xml_partial',
    ]

    @pytest.mark.parametrize("test_filename, test_filetypes, expected", [
        ("", [], True),
        ("", [".mp3"], True),
        ("S01E01_pod", [], True),
        ("S01E01_pod", [".mp3"], True),
        ("S01E01_pod", [".xml"], True),
        ("S01E01_pod", [".ignore"], True),
        ("S01E01_pod", [".partial"], True),
        ("S01E01_pod", [".mp3", '.xml'], False),
        ("S01E01_pod", [".mp3", '.xml', '.jpg'], False),
        ("S01E01_pod", [".mp3", '.xml', ".ignore"], True),
        ("S01E01_pod", ['.xml', ".ignore"], True),
        ("S01E01_pod", [".mp3", ".ignore"], True),
        ("S01E01_pod", [".mp3", '.xml', ".partial"], True),
    ], ids=ids)
    def test_are_ignoring(self, test_filename, test_filetypes, expected):

        ignoring = PodcastDirectoryWalker._are_ignoring(test_filename, test_filetypes)

        assert expected == ignoring
