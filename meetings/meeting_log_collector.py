#!/usr/bin/env python
# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser
import requests
from datetime import datetime
import os
import itertools
import sys


LOG_HOST = 'http://eavesdrop.openstack.org'
JOIN_QUIT = ('joined', 'quit')


class LinkParser(HTMLParser, object):
    def __init__(self):
        super(LinkParser, self).__init__()
        self.href_attrs = []

    def handle_starttag(self, tag, attrs):
        if 'a' in tag and attrs:
            attr, link = attrs[0]
            if attr == 'href':
                self.href_attrs.append(link)


class NormalLogParser(object):
    """
    Parser for #openstack-swift channel
    """
    # NOTE: channel should not starts with slash
    channel = 'irclogs/%23openstack-swift/'
    base_url = 'http://eavesdrop.openstack.org/irclogs/%23openstack-swift/'
    name_wrap = '%s'
    log_ext = 'log.html'

    @property
    def base_url(self):
        return os.path.join(LOG_HOST, self.channel)

    def log_date_of(self, log_name):
        date_str = log_name.split('.')[1]
        parsed = self.split_log_date(date_str)
        log_date = datetime(
            year=int(parsed[0]), month=int(parsed[1]), day=int(parsed[2]))
        return log_date

    def in_range_of(self, start_datetime, end_datetime, log_name):
        # log name should be like swift.2016-09-07-21.00.log.txt
        if log_name == 'latest.log.html':
            return False
        log_date = self.log_date_of(log_name)
        return (start_datetime <= log_date) and (log_date <= end_datetime)

    def split_log_date(self, date_str):
        return date_str.split('-', 3)

    def ext_check(self, log_name):
        return log_name.endswith(self.log_ext)

    def wrap_name(self, name):
        return self.name_wrap % name

    def count_voices(self, contributor_names, log_names):
        count = {}

        sys.stderr.write('PROGRESS...\n')
        for i in range(len(log_names)):
            sys.stderr.write('_')
        sys.stderr.write('\n')

        for i, log_name in enumerate(log_names):
            sys.stderr.write('>')
            alog = os.path.join(self.base_url, log_name)
            log_date = self.log_date_of(log_name)
            resp = requests.get(alog)
            for (line, contributor) in itertools.product(
                    resp.content.split('\n'), contributor_names):
                wrapped_name = self.wrap_name(contributor)
                if wrapped_name in line:
                    # ignoring just join/quit message for the channel
                    for ignore in JOIN_QUIT:
                        if ignore in line:
                            break
                    else:
                        monthly_count = count.setdefault(log_date.month, {})
                        daily_count =\
                            monthly_count.setdefault(log_date.day, {})
                        count_of_the_contributor =\
                            daily_count.setdefault(contributor, 0)
                        daily_count[contributor] =\
                            count_of_the_contributor + 1
        sys.stderr.write('\n')

        return count


class MeetingLogParser(NormalLogParser):
    """
    Parser for #openstack-meeting channel, designed for swift meeting
    :param year: year (integer) to collect the meeting. Currently collecting
                 accross the different years is not supported
    """
    channel = 'meetings/swift/'
    name_wrap = '<%s>'
    log_ext = 'log.txt'

    def __init__(self, year):
        self.year = str(year)

    def split_log_date(self, date_str):
        return date_str.split('-', 4)

    @property
    def base_url(self):
        return os.path.join(LOG_HOST, self.channel, self.year)



if __name__ == '__main__':
    year = 2014
    start_datetime = datetime(year=year, month=1, day=1)
    end_datetime = datetime(year=year, month=12, day=31)
    contributor_names = [
        'kota_', 'm_kazuhiro', 'dmorita', 'hosanai', 'notmyname', 'clayg',
        'acoles', 'tdasilva']
    collect_meeting_log = False

    log_parser =\
        MeetingLogParser(year) if collect_meeting_log else NormalLogParser()
    resp = requests.get(os.path.join(log_parser.base_url))
    parser = LinkParser()
    parser.feed(resp.content)

    log_names = [log_name for log_name in parser.href_attrs
                 if log_parser.ext_check(log_name) and
                 log_parser.in_range_of(start_datetime, end_datetime, log_name)]
    count = log_parser.count_voices(contributor_names, log_names)


    print '<html>'
    print '<body>'

    # all sum
    print str(year) + "年 合計"
    print '<table border="1">'
    print '<tr>' + ''.join(['<th>' + _ + '</th>'
        for _ in ['all'] + contributor_names]) + '</tr>'
    all_sum = {}
    for month in count:
        for day in count[month]:
            for contributor in contributor_names:
                count_sum = all_sum.setdefault(contributor, 0)
                count_sum += count[month][day].setdefault(contributor, 0)
                all_sum[contributor] = count_sum
    print '<tr>' + ''.join(['<td>' + _ + '</td>'
        for _ in ['all'] + [str(all_sum.setdefault(contributor, 0))
        for contributor in contributor_names]]) + '</tr>'
    print '</table>'

    # monthly sum
    print str(year) + "年 月ごと"
    print '<table border="1">'
    print '<tr>' + ''.join(['<th>' + _ + '</th>'
        for _ in ['month'] + contributor_names]) + '</tr>'
    for month in count:
        monthly_sum = {}
        for day in count[month]:
            for contributor in contributor_names:
                count_sum = monthly_sum.setdefault(contributor, 0)
                count_sum += count[month][day].setdefault(contributor, 0)
                monthly_sum[contributor] = count_sum
        print '<tr>' + ''.join(['<td>' + _ + '</td>'
            for _ in [str(month)] + [str(monthly_sum.setdefault(contributor, 0))
            for contributor in contributor_names]]) + '</tr>'
    print '</table>'

    # daily count
    print str(year) + "年 日ごと"
    print '<table border="1">'
    print '<tr>' + ''.join(['<th>' + _ + '</th>'
        for _ in ['day'] + contributor_names]) + '</tr>'
    for month in count:
        for day in count[month]:
            print '<tr>' + ''.join(['<td>' + _ + '</td>'
                for _ in ['/'.join([str(month), str(day)])] +
                [str(count[month][day].setdefault(contributor, 0))
                for contributor in contributor_names]]) + '</tr>'
    print '</table>'

    print '</html>'
    print '</body>'
