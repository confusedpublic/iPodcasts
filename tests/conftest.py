# -*- coding: utf-8 -*-

from ipodcasts import Podcast

def pytest_assertrepr_compare(op, left, right):

    if isinstance(left, Podcast) and isinstance(right, Podcast) and op == "==":
        
        if left.__dict__['_title'] == right.__dict__['_title']:
            title_string = '   title: %s == %s' % (left.__dict__['_title'], right.__dict__['_title'])
        else:
            title_string = '   title: %s != %s' % (left.__dict__['_title'], right.__dict__['_title'])
        if left.__dict__['_series'] == right.__dict__['_series']:
            series_string = '   series: %s == %s' % (left.__dict__['_series'], right.__dict__['_series'])
        else:
            series_string = '   series: %s != %s' % (left.__dict__['_series'], right.__dict__['_series'])
        if left.__dict__['_season_number'] == right.__dict__['_season_number']:
            season_number_string = '   season_number: %s == %s' % (left.__dict__['_season_number'],
                                                                   right.__dict__['_season_number'])
        else:
            season_number_string = '   season_number: %s != %s' % (left.__dict__['_season_number'],
                                                                   right.__dict__['_season_number'])
        if left.__dict__['_episode_number'] == right.__dict__['_episode_number']:
            episode_number_string = '  episode_number:  %s == %s' % (left.__dict__['_episode_number'],
                                                                     right.__dict__['_episode_number'])
        else:
            episode_number_string = '   episode_number: %s != %s' % (left.__dict__['_episode_number'],
                                                                     right.__dict__['_episode_number'])
        if left.__dict__['_file_path'] == right.__dict__['_file_path']:
            file_path_string = '   file_path: %s == %s' % (left.__dict__['_file_path'], right.__dict__['_file_path'])
        else:
            file_path_string = '   file_path: %s != %s' % (left.__dict__['_file_path'], right.__dict__['_file_path'])
        if left.__dict__['_xml_path'] == right.__dict__['_xml_path']:
            xml_path_string = '   xml_path: %s == %s' % (left.__dict__['_xml_path'], right.__dict__['_xml_path'])
        else:
            xml_path_string = '   xml_path: %s != %s' % (left.__dict__['_xml_path'], right.__dict__['_xml_path'])

        return ['Comparing Podcast instances:',
                title_string,
                series_string,
                season_number_string,
                episode_number_string,
                file_path_string,
                xml_path_string
                ]