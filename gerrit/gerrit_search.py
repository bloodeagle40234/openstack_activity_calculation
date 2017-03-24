import requests
import json
from datetime import datetime

gerrit_url = 'https://review.openstack.org/changes/?q=%s'
# gerrit_query = {'status': 'open',
# gerrit_query = {'status': ('merged', ),
gerrit_query = {'status': ('open', 'merged', 'abandone'),
                'project': ('openstack/swift', 'openstack/pyeclib',
                            'openstack/liberasurecode',
                            'openstack/swift3', 'openstack/storlets',
                            'stackforge/swift3'),
                'owner': 'Kota'}

# for swift3 search
# gerrit_query = {'project': 'stackforge/swift3',
#                 'status': 'merged'}
headers = {'Accept': 'application/json',
           'Accept-Encoding': 'gzip'}
OPENSTACK_PREFIX = 'opesntack/'

"""
Matthew's sample:
status:open+age:4week+(label:Verified<=-1,jenkins+OR+label:Code-Review<=-1)+NOT+label:Workflow<=-1+(project:openstack/swift+OR+project:openstack/python-swiftclient+OR+project:openstack/swift-python-agent+OR+project:openstack/swift-bench+OR+project:openstack/swift-specs)+status:open+NOT+label:Code-Review<=-2&o=DETAILED_ACCOUNTS
"""


def get_age(date):
    """
    parm: date: the format must be YYYY/MM/DD.
    """
    now = datetime.now()
    expect = datetime.strptime(date, '%Y/%m/%d')
    return '%ddays' % (now - expect).days


def generate_or_query(key, values):
    items = []
    for value in values:
        items.append('%s:%s' % (key, value))
    return '(%s)' % '+OR+'.join(items)


def get_query_string(query_dict, prefix=''):
    items = []
    conj = '+'
    for key, value in query_dict.iteritems():
        if isinstance(value, tuple):
            string = generate_or_query(key, value)
        else:
            string = '%s:%s' % (key, value)
        items.append(string)

    if prefix:
        conj = '+%s+' % prefix

    query_string = conj.join(items)
    if prefix:
        query_string = '%s+%s' % (prefix, query_string)
    return query_string


def main():
    age = get_age('2016/04/01')
    query = get_query_string(gerrit_query)
    not_query = get_query_string({'age': age}, 'NOT')
    query += '+%s' % not_query
    session = requests.Session()
    resp = session.get(gerrit_url % query,
                       headers=headers)
    changes = json.loads(resp.text[4:])
    for change in sorted(changes, key=lambda k: k['created']):
        change['project'] = change['project'][len(OPENSTACK_PREFIX):]
        title = '%(project)s: %(subject)s' % change
        date = change['created'].split(' ')[0].replace('-', '/')
        print(','.join([date, '', title]))


if __name__ == '__main__':
    main()
