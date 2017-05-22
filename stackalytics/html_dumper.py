import requests
import os.path
import json

base_url = 'http://stackalytics.com/api/'
version = '1.0'
api = 'stats'
base_request_url = os.path.join(base_url, version, api)

releases = [
    'all',
    'austin', 'bexar', 'cactus', 'diablo', 'essex',
    'folsom', 'grizzly', 'havana', 'icehouse', 'juno',
    'kilo', 'liberty', 'mitaka', 'newton', 'ocata',
    'pike']


class BaseCollector(object):
    page_size = 100

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
            resp = requests.get(
                os.path.join(base_url, version, 'activity'), filter_params)
            content = json.loads(resp.content)
            activities.extend(content['activity'])
            filter_params['start_record'] += self.page_size
            if len(content['activity']) == 0:
                break
        return activities

    def collect_commit_info(self, releases=['all']):
        """
        :param releases: which release caller wants to collect
        :return: a dict which maps release -> user_id -> commit info
        """
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

    def dump_result(self, result, dump_format='html'):
        """
        :param result: a result dict that maps reslease -> user_id -> value
        :param dump_format:
        """
        if dump_format not in ('html', 'csv'):
            raise ValueError('dump_format is supported only for html or csv')

        # release_to_activity_list is a dict to map a release to user
        # activities (perhaps, we don't have to keep the release for the key
        # because each row keep the release name in the 1st column)
        release_to_activity_list = dict()

        for release, result_info in result.items():
            row_list = [release]
            for user_id in self.user_id_list:
                # N.B. the result set may be already filtered when
                # collecting the result but for safety, use .get and set
                # 0 if the user id not found in the dict)
                row_list.append(str(result_info.get(user_id, 0)))
            release_to_activity_list[release] = row_list

        if dump_format == 'csv':
            # dump as csv
            print(','.join(self.titles()))
            for _, row_list in release_to_activity_list.items():
                print(','.join(row_list))
        else:
            # dump as html
            title_row = '<tr>%s</tr>' % ''.join(
                ['<th>%s</th>' % title for title in self.titles()])
            body_rows = ''
            for _, row_list in release_to_activity_list.items():
                body_rows += '<tr>%s</tr>' % ''.join(
                    ['<td>%s</td>' % item for item in row_list])

            print('<html><body><table border="1">%s%s</table></body></html>'
                  % (title_row, body_rows))

    def titles(self):
        """
        :return: a title row list which is like as
            ['release', 'user-id1', 'user-id2'....]
        """
        title_row = ['release']
        title_row.extend(self.user_id_list)
        return title_row


class CommitCollector(BaseCollector):
    user_id_list = [
        'tsuyuzaki-kota', 'miyahara-kazuhiro', 'notmyname', 'clay-gerrard',
        'alistair-coles', 'cschwede', 'thiagodasilva']

    def __init__(self):
        self.filter_params = {
            'metric': 'commits',
            'page_size': self.page_size,
            'start_record': 0}

    def commit_count(self, commit_info_dict):
        """
        summarize
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


class LoCCollector(BaseCollector):
    user_id_list = [
        'tsuyuzaki-kota', 'miyahara-kazuhiro', 'notmyname', 'clay-gerrard',
        'alistair-coles', 'cschwede', 'thiagodasilva']

    def lines_of_code(self, commit_info_dict):
        """
        summarize
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


class ReviewCollector(object):
    def collect_stats(self, release):
        filter_params = {'release': release}
        filter_params.update(self.base_filter_params)
        resp = requests.get(
            os.path.join(base_request_url, self.url_tail), filter_params)
        stats_list = json.loads(resp.content)['stats']
        return stats_list

    def review_counts(self):
        review_counts = {}
        for release in releases:
            stats_per_release = self.collect_stats(release)
            review_counts_per_release = {}
            for stat in stats_per_release:
                if stat['name'] not in self.target_names:
                    continue
                # review count
                review_counts_per_release[stat['name']] = stat['metric']
            review_counts[release] = review_counts_per_release
        return review_counts


class EngineerReviewCollector(ReviewCollector):
    # dump review_counts per engineer
    url_tail = 'engineers'
    base_filter_params = {}
    target_names = [
        'Kota Tsuyuzaki', 'Kazuhiro MIYAHARA', 'Samuel Merritt',
        'Clay Gerrard', 'Alistair Coles', 'John Dickinson', 'Pete Zaitcev',
        'Matthew Oliver', 'Greg Holt', 'Christian Schwede', 'Peter Portante',
        'Darrell Bishop', 'Tim Burke', 'Thiago da Silva', 'David Goetz',
        'Chmouel Boudjnah', 'paul luse', 'Mike Barton', 'Chuck Thier',
        'Janie Richling', 'Greg Lange', 'Hisashi Osanai', 'Mahati']


class ModuleReviewCollector(ReviewCollector):
    # dump review_counts per module
    url_tail = 'modules'
    base_filter_params = {}
    target_names = ['swift', 'nova', 'neutron', 'swift3', 'storlets']


class CompanyReviewCollector(ReviewCollector):
    # dump review_counts per company
    url_tail = 'companies'
    base_filter_params = {'module': 'swift'}
    target_names = [
        'NTT', 'SwiftStack', 'Red Hat', 'HP', 'HPE', 'Rackspace', 'IBM']


if __name__ == '__main__':
    # review_counts_collector = CompanyReviewCollector()
    # review_counts_collector.dump_review_counts_in_html()

    commit_collector = CommitCollector()
    info = commit_collector.collect_commit_info(['pike'])

    # commit
    # result = commit_collector.commit_count(info)
    # commit_collector.dump_result(result)

    # loc
    loc_collector = LoCCollector()
    result = loc_collector.lines_of_code(info)
    loc_collector.dump_result(result)
