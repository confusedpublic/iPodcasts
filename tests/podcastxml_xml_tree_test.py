# -*- coding: utf-8 -*-

import pytest
from lxml import etree

from ipodcasts import PodcastXML


class TestPodcastXML(object):

    def test_no_file(self):

        p_xml = PodcastXML()

        with pytest.raises(OSError):
            p_xml.xml_tree = '/tmp/does/not/exist.xml'

    def test_empty_file(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write("")
        p_xml = PodcastXML()

        with pytest.raises(etree.XMLSyntaxError):
            p_xml.xml_tree = str(tmp_xml)

    def test_fake_data(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write("<xml>\n\t<fake>test</fake>\n</xml>")
        p_xml = PodcastXML()

        p_xml.xml_tree = str(tmp_xml)

        assert isinstance(p_xml.xml_tree, etree._ElementTree)
        assert len(p_xml.xml_tree.findall("fake")) == 1
