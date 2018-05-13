# -*- coding: utf-8 -*-
import socket
import logging
from lxml import etree


def get_ip():
    """ Get the local ip address of the server running ipodcasts """

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
    return ip


# Needed for the owner's email address in the podcast's xml file.
email = 'dave.race@gmail.com'


logger = logging.getLogger(__name__)


class PodcastXML(object):

    def __init__(self, email=email, get_iplayer_ns_string="http://linuxcentre.net/xmlstuff/get_iplayer",
                 pod_ns="http://www.itunes.com/dtds/podcast-1.0.dtd", pod_ns_key="itunes",
                 tags_needing_ns=('owner', 'name', 'email', 'image', 'author', 'explicit', 'summary'),
                 new_show_template=None):
        self.get_iplayer_ns = {'xmlns': get_iplayer_ns_string}
        self.pod_ns = pod_ns
        self.pod_ns_key = pod_ns_key
        self.pod_ns_tag = "{%s}" % self.pod_ns
        # And generate the namespace map for turning the literal namespace into the key/abbreviation later
        self.namespace_map = {self.pod_ns_key: self.pod_ns}
        self.needs_namespaces = tags_needing_ns
        self.new_show_template = {
            'explicit': 'no',
            'owner': {
                'email': email
            },
            'lastBuildDate': None,
            'language': 'en-gb',
            'ttl': 10,
            'image_p': {}
        } if new_show_template is None else new_show_template
        self._xml_tree = None

    @property
    def xml_tree(self):
        return self._xml_tree

    @xml_tree.setter
    def xml_tree(self, xml_file_path):
        # TODO: add episode xml validation here
        if not self.xml_tree:
            self._xml_tree = etree.parse(xml_file_path)

    def _tag_text(self, wanted_tag):
        """ Search the element tree, with namespace, return tag text
        """

        tag = self.xml_tree.find("xmlns:{}".format(wanted_tag), namespaces=self.get_iplayer_ns)

        if tag is None:
            logger.debug(etree.tostring(self.xml_tree))
            raise ValueError("Did not find the tag")
        else:
            return tag.text if tag.text else ""
