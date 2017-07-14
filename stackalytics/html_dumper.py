import requests
import os.path
import json

BASE_URL = 'http://stackalytics.com/api/'
VERSION = '1.0'
api = 'stats'

releases = [
    'all',
    'austin', 'bexar', 'cactus', 'diablo', 'essex',
    'folsom', 'grizzly', 'havana', 'icehouse', 'juno',
    'kilo', 'liberty', 'mitaka', 'newton', 'ocata',
    'pike']


class CommitCollector(object):
    page_size = 100
    user_id_list = [
        'tsuyuzaki-kota', 'miyahara-kazuhiro', 'notmyname', 'clay-gerrard',
        'alistair-coles', 'cschwede', 'thiagodasilva']

    def __init__(self, user_id_list=None):
        self.filter_params = {
            'metric': 'commits',
            'page_size': self.page_size,
            'start_record': 0}
        self.user_id_list = user_id_list or self.user_id_list
        self.url = os.path.join(BASE_URL, VERSION, 'activity')

    def collect_activities(self, user_id, release, params=None):
        """
        collect user activiety for the specific release

        :param user_id: launchpad user id to collect
        :param release: release name of openstack to collect, "all" can be
            allowed to collect all activities
        :param params: parameter dict
        :return activities: a list of activity dict
        """
        params = params or {}
        filter_params = {'user_id': user_id, 'release': release}
        filter_params.update(params)
        activities = []
        while True:
            resp = requests.get(self.url, filter_params)
            content = json.loads(resp.content)
            activities.extend(content['activity'])
            filter_params['start_record'] += self.page_size
            if len(content['activity']) == 0:
                break
        return activities

    def collect_commit_info(self, releases=None):
        """
        :param releases: which release caller wants to collect
        :return: a dict which maps release -> user_id -> commit info
        """
        releases = releases or ['all']
        commits = {}
        for release in releases:
            commits_per_release = {}
            for user_id in self.user_id_list:
                activities_per_user_and_release = self.collect_activities(
                    user_id, release, self.filter_params)
                commits_per_user_and_release = []
                for activity in activities_per_user_and_release:
                    commits_per_user_and_release.append({
                        'author': activity['author_name'],
                        'lines_of_code': activity['loc'],
                        'first_commit_date': activity['commit_date'],
                        'merge_date': activity['date'],
                        'subject': activity['subject']})
                commits_per_release[user_id] = commits_per_user_and_release
            commits[release] = commits_per_release
        return commits

    @property
    def titles(self):
        """
        :return: a title row list which is like as
            ['release', 'user-id1', 'user-id2'....]
        """
        titles = ['release']
        titles.extend(self.user_id_list)
        return titles


def dump_result(result, titles, dump_format='html'):
    """
    :param result: a result dict that maps reslease -> user_id -> value
    :param titles: a list of title row items. Note that titles[1:] will
        be used to find items to dump
    :param dump_format: html or csv
    """
    if dump_format not in ('html', 'csv'):
        raise ValueError('dump_format is supported only for html or csv')

    # release_to_activity_list is a dict to map a release to user
    # activities (perhaps, we don't have to keep the release for the key
    # because each row keep the release name in the 1st column)
    release_to_activity_list = dict()
    keys = titles[1:]

    for release, result_info in result.items():
        row_list = [release]
        for key in keys:
            # N.B. the result set may be already filtered when
            # collecting the result but for safety, use .get and set
            # 0 if the key not found in the dict)
            row_list.append(str(result_info.get(key, 0)))
        release_to_activity_list[release] = row_list

    if dump_format == 'csv':
        # dump as csv
        print(','.join(titles))
        for _, row_list in release_to_activity_list.items():
            print(','.join(row_list))
    else:
        # dump as html
        title_row = '<tr>%s</tr>' % ''.join(
            ['<th>%s</th>' % title for title in titles])
        body_rows = ''
        for _, row_list in release_to_activity_list.items():
            body_rows += '<tr>%s</tr>' % ''.join(
                ['<td>%s</td>' % item for item in row_list])

        print('<html><body><table border="1">%s%s</table></body></html>'
              % (title_row, body_rows))


def commit_count(commit_info_dict):
    """
    helper fucntion to summarize all commit count from raw commit info
    :param commit_info_dict: a raw infor dict that collect_commit_info
        returns
    :return: summary info that maps release -> user_id -> value
    """
    commit_counts = {}
    for release, commit_dict in commit_info_dict.items():
        commit_counts_per_release = {}
        for user_id, commit_list in commit_dict.items():
            commit_counts_per_release[user_id] = len(commit_list)
        commit_counts[release] = commit_counts_per_release
    return commit_counts


def lines_of_code(commit_info_dict):
    """
    helper fucntion to summarize all lines of code from raw commit info
    :param commit_info_dict: a raw infor dict that collect_commit_info
        returns
    :return: summary info that maps release -> user_id -> value
    """
    lines_of_code = {}
    for release, commit_dict in commit_info_dict.items():
        user_to_loc = {}
        for user_id, commit_list in commit_dict.items():
            user_to_loc[user_id] = sum(
                commit['lines_of_code'] for commit in commit_list)
        lines_of_code[release] = user_to_loc
    return lines_of_code


def review_counts(stat_info_dict):
    """
    helper fucntion to summarize all from raw stat info from ReviewCollector
    :param stat_info_dict: a raw infor dict that collect_stat_info
        returns
    :return: summary info that maps release -> identifier
        (e.g. user id, company_name) -> value
    """
    review_counts = {}
    for release, stat_dict in stat_info_dict.items():
        review_counts_per_release = {}
        for key, stat in stat_dict.items():
            # review count
            review_counts_per_release[key] = stat['metric']
        review_counts[release] = review_counts_per_release
    return review_counts


class ReviewCollector(object):
    def __init__(self):
        self.url = os.path.join(BASE_URL, VERSION, 'stats', self.category)

    def collect_stat_info(self, releases=None, params=None):
        """
        TODO perhaps, we could make a BaseCollector for collecting activities
        :param release: release name of openstack to collect, "all" can be
            allowed to collect all activities
        :param params: parameter dict
        """
        releases = releases or ['all']
        params = params or {}
        release_to_stat = {}
        for release in releases:
            filter_params = {'release': release}
            filter_params.update(params)
            resp = requests.get(self.url, filter_params)
            stats_list = json.loads(resp.content)['stats']
            # filter stats only in targets
            # N.B. it could be worth to make this as query
            stats_list = dict(
                [(stat['name'], stat) for stat in stats_list
                 if stat['name'] in self.targets])
            release_to_stat[release] = stats_list
        return release_to_stat

    @property
    def titles(self):
        """
        :return: a title row list which is like as
            ['release', 'user-id1', 'user-id2'....]
        """
        titles = ['release']
        titles.extend(self.targets)
        return titles


class EngineerReviewCollector(ReviewCollector):
    # dump review_counts per engineer
    category = 'engineers'
    targets = [
        'Kota Tsuyuzaki', 'Kazuhiro MIYAHARA', 'Samuel Merritt',
        'Clay Gerrard', 'Alistair Coles', 'John Dickinson', 'Pete Zaitcev',
        'Matthew Oliver', 'Greg Holt', 'Christian Schwede', 'Peter Portante',
        'Darrell Bishop', 'Tim Burke', 'Thiago da Silva', 'David Goetz',
        'Chmouel Boudjnah', 'paul luse', 'Mike Barton', 'Chuck Thier',
        'Janie Richling', 'Greg Lange', 'Hisashi Osanai', 'Mahati']


class ModuleReviewCollector(ReviewCollector):
    # dump review_counts per module
    category = 'modules'
    targets = ['swift', 'nova', 'neutron', 'swift3', 'storlets']


class CompanyReviewCollector(ReviewCollector):
    # dump review_counts per company
    category = 'companies'
    targets = [
        'NTT', 'SwiftStack', 'Red Hat', 'HP', 'HPE', 'Rackspace', 'IBM']
    # N.B. right now *params* is not used
    params = {'module': 'swift'}


if __name__ == '__main__':
    # reviews
    review_collector = EngineerReviewCollector()
    info = review_collector.collect_stat_info(['pike'])
    result = review_counts(info)
    dump_result(result, review_collector.titles)

    # commit_collector = CommitCollector()
    # info = commit_collector.collect_commit_info(['pike'])

    # commit
    # result = commit_count(info)
    # dump_result(result, commit_collector.titles)

    # loc
    # result = lines_of_code(info)
    # dump_result(result, commit_collector.titles)
