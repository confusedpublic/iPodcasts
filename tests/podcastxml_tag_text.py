# -*- coding: utf-8 -*-

import pytest

from ipodcasts import PodcastXML


class TestPodcastXML(object):

    def test_no_xmlns_tag_exists(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                      '<fake>test</fake>')
        p_xml = PodcastXML()
        p_xml.xml_tree = str(tmp_xml)

        with pytest.raises(ValueError):
            p_xml._tag_text("fake")

    def test_xmlns_tag_doesnt_exist(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                      '<program_meta_data xmlns="eg_namespace">\n\t<fake>test</fake>\n'
                      '</program_meta_data>')
        p_xml = PodcastXML()
        p_xml.xml_tree = str(tmp_xml)

        with pytest.raises(ValueError):
            p_xml._tag_text("test")

    def test_xmlns_and_tag(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                      '<program_meta_data xmlns="eg_namespace">\n\t<fake>test</fake>\n'
                      '</program_meta_data>')
        p_xml = PodcastXML(get_iplayer_ns_string="eg_namespace")

        p_xml.xml_tree = str(tmp_xml)

        assert "test" == p_xml._tag_text("fake")

    def test_xmlns_and_empty_tag(self, tmpdir):

        tmp_xml = tmpdir.join('test.xml')
        tmp_xml.write('<?xml version="1.0" encoding="utf-8" ?>\n'
                      '<program_meta_data xmlns="eg_namespace">\n\t'
                        '<fake>test</fake>\n\t'
                        '<empty></empty>\n'
                      '</program_meta_data>')
        p_xml = PodcastXML(get_iplayer_ns_string="eg_namespace")

        p_xml.xml_tree = str(tmp_xml)

        assert "" == p_xml._tag_text("empty")
