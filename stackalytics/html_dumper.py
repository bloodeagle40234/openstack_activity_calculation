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

class CommitCollector(object):
    user_id_list = [
        'tsuyuzaki-kota', 'miyahara-kazuhiro', 'notmyname', 'clay-gerrard',
        'alistair-coles', 'cschwede', 'thiagodasilva']

    #user_id_list = [
    #    'tsuyuzaki-kota', 'miyahara-kazuhiro', 'marek-kaleta', 'charles0126',
    #    'tuanla', 'romain-ledisez', 'kellerbr', 'mahati-chamarthy',
    #    'confisurya', 'diazjf', 'junboli', 'jsbryant', 'v-iswarya',
    #    'wanghongtaozz', 'vancsics', 'guojianhua', 'mohit-motiani', 'dolph',
    #    'janonymous', 'jeremy.zhang', 'kevin-zhao', 'sacpatil', 'miethe',
    #    'harinipradeep27', 'jrichli', 'rahulunair', 'travis-mcpeak',
    #    'clay-gerrard', 'chen-xing', 'joel-wright-k', 'alistair-coles',
    #    'o-tony', 'tnovacik-6', '1-tim-z', 'lidong007', 'thurloat',
    #    'paul-dardeau', 'jaegerandi', 'yuhui', 'dims-v', 'indicoliteplus',
    #    'nandini-tata', 'tuhv', 'pavel.kvasnicka@firma.seznam.cz', 'jaosorior',
    #    'ericwb', 'yangjd', 'onovy', 'falk-reimann', 'alexisl', 'alecuyer',
    #    'arnaud-morin', 'briancline', 'dunght', 'treinish', 'torgomatic',
    #    'notmyname', 'karenc', 'richard-hawkins', 'cschwede', 'peterlisak',
    #    'zhanghj', 'trananhkma', 'matt-0', 'gabor.antal', 'sharat-sharma',
    #    'kaitlin-farr', 'yin-zheng', 'glonlas', 'thiagodasilva', 'caowei-e',
    #    'aerwin3', 'hongkai', 'zaitcev', 'hoangcx']

    page_size = 100
    base_filter_params = {
        'metric': 'commits', 'page_size': page_size, 'start_record': 0}

    def collect_activities_per_user(self, user_id, release):
        filter_params = {'user_id': user_id, 'release': release}
        filter_params.update(self.base_filter_params)
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

    def commits(self):
        commits = {}
        for release in releases:
            commits_per_release = {}
            for user_id in self.user_id_list:
                activities_per_user_and_release =\
                    self.collect_activities_per_user(user_id, release)
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

    def table_headers(self):
        return ['release'] + self.user_id_list

    def table_bodies(self, result, release):
        return [release] + [str(result[release][user_id])
            for user_id in self.user_id_list]

    def dump_result_in_csv(self, result, delimiter=','):
        print delimiter.join(self.table_headers())
        for release in releases:
            print delimiter.join(self.table_bodies(result, release))

    def dump_result_in_html(self, result):
        print '<html>'
        print '<body>'
        print '<table border="1">'

        print '<tr>'
        print ''.join(['<th>' + _ + '</th>' for _ in self.table_headers()])
        print '</tr>'

        for release in releases:
            print '<tr>'
            print ''.join(['<td>' + _ + '</td>'
                for _ in self.table_bodies(result, release)])
            print '</tr>'

        print '</table>'
        print '</body>'
        print '</html>'

    def lines_of_code_sum(self):
        commits = self.commits()
        lines_of_code_sum = {}
        for release in commits:
            lines_of_code_sum_per_release = {}
            for user_id in commits[release]:
                lines_of_code_sum_per_user_and_release = 0
                for commit in commits[release][user_id]:
                    lines_of_code_sum_per_user_and_release +=\
                        commit['lines_of_code']
                lines_of_code_sum_per_release[user_id] =\
                    lines_of_code_sum_per_user_and_release
            lines_of_code_sum[release] = lines_of_code_sum_per_release
        return lines_of_code_sum

    def dump_lines_of_code_sum_in_csv(self):
        self.dump_result_in_csv(self.lines_of_code_sum())

    def dump_lines_of_code_sum_in_html(self):
        self.dump_result_in_html(self.lines_of_code_sum())

    def commit_counts(self):
        commits = self.commits()
        commit_counts = {}
        for release in commits:
            commit_counts_per_release = {}
            for user_id in commits[release]:
                commit_counts_per_release[user_id] =\
                    len(commits[release][user_id])
            commit_counts[release] = commit_counts_per_release
        return commit_counts

    def dump_commit_counts_in_csv(self):
        self.dump_result_in_csv(self.commit_counts())

    def dump_commit_counts_in_html(self):
        self.dump_result_in_html(self.commit_counts())


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

    def table_headers(self):
        return ['release'] + self.target_names

    def table_bodies(self, stats, release):
        return [release] + [str(stats[release].setdefault(target_name, 0))
            for target_name in self.target_names]

    def dump_review_counts_in_csv(self, delimiter=','):
        stats = self.review_counts()
        print delimiter.join(self.table_headers())
        for release in releases:
            print delimiter.join(self.table_bodies(stats, release))

    def dump_review_counts_in_html(self):
        stats = self.review_counts()

        print '<html>'
        print '<body>'
        print '<table border="1">'

        print '<tr>'
        print ''.join(['<th>' + _ + '</th>' for _ in self.table_headers()])
        print '</tr>'

        for release in releases:
            print '<tr>'
            print ''.join(['<td>' + _ + '</td>'
                for _ in self.table_bodies(stats, release)])
            print '</tr>'

        print '</table>'
        print '</body>'
        print '</html>'


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
    #review_counts_collector = CompanyReviewCollector()
    #review_counts_collector.dump_review_counts_in_html()

    commit_collector = CommitCollector()
    commit_collector.dump_lines_of_code_sum_in_html()

