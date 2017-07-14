import six

if six.PY2:
    from HTMLParser import HTMLParser
else:
    from html.parser import HTMLParser

import requests
from datetime import datetime
import os


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

    def latter_than(self, base_datetime, log_name):
        # log name should be like swift.2016-09-07-21.00.log.txt
        if log_name == 'latest.log.html':
            return False
        date_str = log_name.split('.')[1]
        parsed = self.split_log_date(date_str)
        log_date = datetime(
            year=int(parsed[0]), month=int(parsed[1]), day=int(parsed[2]))
        return log_date > base_datetime

    def split_log_date(self, date_str):
        return date_str.split('-', 3)

    def ext_check(self, log_name):
        return log_name.endswith(self.log_ext)

    def wrap_name(self, name):
        return self.name_wrap % name


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


def collect_my_voice(whoami, logs):
    voices = []
    for alog in logs:
        resp = requests.get(alog)
        for line in resp.content.split('\n'):
            if whoami in line:
                # ignoring just join/quit message for the channel
                for ignore in JOIN_QUIT:
                    if ignore in line:
                        break
                else:
                    voices.append(line)
    return voices


if __name__ == '__main__':
    year = 2017
    # choose MeetingLogParser or NormalLogParser
    log_parser = MeetingLogParser(year)
    # log_parser = NormalLogParser()
    base_datetime = datetime(year=year, month=7, day=7)
    resp = requests.get(os.path.join(log_parser.base_url))
    parser = LinkParser()
    parser.feed(resp.content)
    logs = [os.path.join(log_parser.base_url, item)
            for item in parser.href_attrs
            if log_parser.ext_check(item) and
            log_parser.latter_than(base_datetime, item)]
    voices = collect_my_voice(log_parser.wrap_name('kota_'), logs)
    # join is the count of logs (er - just a # of collected logs,
    # it may not join count actually)
    print('# of join: %s' % len(logs))
    # voice is the count of lines your name appeared in the line.
    # that can contain the responses for you from other people.
    print('# of voices: %s' % len(voices))
