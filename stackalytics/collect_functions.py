import requests
import os.path
import json

base_url = 'http://stackalytics.com/api/'
version = '1.0'
api = 'stats'
base_request_url = os.path.join(base_url, version, api)


def collect_engineers(company):
    """
    :param company: company name string
    """
    # so let's get the engineers working for NTT
    # Note that if we don't suggest as 'release': 'all', it seems to work only
    # for the newest release.
    params = {'company': company, 'release': 'all'}
    resp = requests.get(os.path.join(base_request_url, 'engineers'), params)
    # try to get all engineers' name
    engineer_list = json.loads(resp.content)['stats']
    return [engineer['name'] for engineer in engineer_list]


def collect_engineer_activities(engineer_id, metric):
    """
    :param engineer_id: engineer_id string which is used at stackalytics
    :param metric: the metric you want to collect from stackalytics
    :return: activities list
    """
    # oh my, the activity request is GET /api/v1.0/activity so no 'stats'
    # important parameters:  page_size and start_record parameters
    page_size = 100
    base_params = {'user_id': engineer_id, 'release': 'all',
                   'page_size': page_size,
                   'start_record': 0, 'metric': metric}

    resp = requests.get(
        os.path.join(base_url, version, 'activity'), base_params)
    content = json.loads(resp.content)
    activities = content['activity']
    got_records = len(activities)

    # if the records are over in the page, try to retrieve the rest for times.
    while got_records:
        base_params['start_record'] += page_size
        resp = requests.get(
            os.path.join(base_url, version, 'activity'), base_params)
        content = json.loads(resp.content)
        more_activities = content['activity']
        activities.extend(more_activities)
        got_records = len(more_activities)

    return activities


if __name__ == '__main__':
    # here is example of each functions
    print('base_request_url: %s' % base_request_url)
    print(collect_engineers('NTT'))
    activities = collect_engineer_activities('tsuyuzaki-kota', 'commits')
    print('total commits activities for all release: %s' % len(activities))
