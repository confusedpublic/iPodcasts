# Podcast_XML

Author: Dave Race

Automatically generate podcast feed xml to be hosted on home server for bbc radio podcasts downloaded by get_iplayer.

Requirements:
LXML - For generating, parsing and editing XML
BeautifulSoup4 - For webscraping for information on the programmes not included in the episode's XML files

Relevant get_iplayer Settings:
tag_podcast_radio 1 # This automatically sets the ID3 tag to podcast for downloaded radio shows
whitespace 0 # This can be set to 1 globally, but needs to be set to 0 for the radio shows, so that the urls work in the XML feed
