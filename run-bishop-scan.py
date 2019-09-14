import requests
import urllib3
import argparse
from datetime import datetime
import sys
import os
import time
import json


SUCCESS = 1
FAILURE = 2
IN_PROGRESS = 3
NOT_STARTED = 4
STARTED = 5
STOPPED = 6


class DistributionSystem:
    """
    Base class for various distribution systems such HckeyApp, Firebase, AppsFlayer, etc
    """
    url = ''
    download_path = ''

    def __init__(self, app_identifier, app_version):
        self.app_identifier = app_identifier
        self.app_version = app_version

    def download_app(self):
        pass


class HockeyApp(DistributionSystem):
    """
    Downloading application from HockeyApp distribution system
    """
    url = 'https://rink.hockeyapp.net/api/2'
    download_path = 'downloaded_apps'

    def __init__(self, token, app_bundle, app_identifier, version):
        super().__init__(app_bundle, version)

        self.app_identifier = app_identifier
        self.auth_header = {'X-HockeyAppToken': token}

    def get_apps(self):
        """
        Get list of available applications
        :return: list of all applications (dict)
        """
        log.info('HockeyApp - Get list of available applications')
        response = requests.get('{0}/{1}'.format(self.url, 'apps'), headers=self.auth_header)
        if response.status_code != 200:
            log.error('HockeyApp - Error while getting application list, status code: {0}'.format(response.status_code))
            sys.exit(4)

        app_list = response.json()
        return app_list.get('apps', [])

    def get_versions_info(self):
        """
        Get all available versions of current application
        :return: list of versions (dict)
        """
        log.info('HockeyApp - Get all available versions of current application')
        if not self.app_identifier:
            for application in self.get_apps():
                if application['bundle_identifier'] != self.app_identifier:
                    continue
                self.app_identifier = application['public_identifier']

        versions_info_url = '{0}/{1}/{2}/{3}'.format(self.url, 'apps', self.app_identifier, 'app_versions')
        response = requests.get(versions_info_url, headers=self.auth_header)
        if response.status_code != 200:
            log.error('HockeyApp - Error while getting application versions info, status code: {0}'.format(response.status_code))
            sys.exit(4)

        return response.json().get('app_versions', [None])

    def get_version(self):
        """
        Return specified version of application
        :return: dict() with metainfo about application version
        """
        log.info('HockeyApp - Get data about specified version')
        if self.app_version == 'latest':
            application_version = self.get_versions_info()[0]
            return application_version

        for version in self.get_versions_info():
            if version['version'] != self.app_version:
                continue

            application_version = version

            return application_version

    def download_app(self):
        """
        Download application
        :return:
        """
        application_for_download = self.get_version()
        if not application_for_download:
            log.error('HockeyApp - Error while getting specified application version, exit')
            sys.exit(4)

        download_url = '{0}?format=apk'.format(application_for_download['download_url'].replace('/apps/', '/api/2/apps/'))
        log.info('HockeyApp - Start download application {0} with version {1}'.format(
            self.app_identifier,
            application_for_download['version']))

        response = requests.get(download_url, headers=self.auth_header, allow_redirects=True)
        if response.status_code != 200:
            log.error('HockeyApp - Failed to download application. Request return status code: {0}'.format(response.status_code))
            sys.exit(4)

        file_name = '{0}-{1}.apk'.format(self.app_identifier, application_for_download['version'])
        path_to_save = os.path.join(self.download_path, file_name)

        if not os.path.exists(self.download_path):
            os.mkdir(self.download_path)

        with open(path_to_save, 'wb') as file:
            file.write(response.content)

        log.info('HockeyApp - Download application successfully completed to {0}'.format(path_to_save))

        return path_to_save


class Bishop:
    """
    Class for interact with Bishop system throw REST API
    """
    def __init__(self, base_url, token, file, profile, testcase):
        self.report_path = 'bishop_scan_report.json'
        self.headers = {'Access-token': token}
        self.url = base_url
        self.apk_file = file
        self.profile = profile
        self.testcase = testcase

    def get(self, url):
        """
        Get method for Bishop REST API.
        Made 3 attempts before fail the script
        :param url: url to get
        :return: response
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code not in (200, 201):
            for i in range(2):
                time.sleep(3)
                log.info('Error in request, status code: {0}. Try to get info one more time. Attempt: {1}'.format(
                    response.status_code, i))
                response = requests.get(url, headers=self.headers)
                if response.status_code in (200, 201):
                    break

        return response

    def _response_json(self, response):
        """
        Get Json data from response. If something wrong exit with error code 5
        :param response:
        :return:
        """
        try:
            return response.json()
        except Exception as e:
            log.error('Error when get json from response: {0}. Response status: {1}'.format(e, response.status_code))
            sys.exit(5)

    def start_scan(self):
        """
        Start automated scan throw REST API
        :return: scan info (dict)
        """
        if not os.path.exists(self.apk_file):
            log.error('APK not exist at file path. exit with error code 2')
            sys.exit(2)

        multipart_form_data = {
            'file': (os.path.split(self.apk_file)[-1], open(self.apk_file, 'rb')),
            'profile_id': (None,self.profile),
            'testcase_id': (None,self.testcase)
        }

        scan_response = requests.post('{0}/rest/scan/cd'.format(self.url), headers=self.headers, files=multipart_form_data)

        scan_object = self._response_json(scan_response)
        if scan_response.status_code != 201:
            log.error('Scan start error: {0}'.format(scan_object.get('message', 'N/A')))
            return False

        return scan_object.get('id', False)

    def get_scan_status(self, scan_id):
        """
        Get scan status from current scan Id
        :param scan_id: Scan ID to get status
        :return:
        """
        scan_response = self.get('{0}/rest/scanlist/{1}'.format(self.url, scan_id))
        scan_object = self._response_json(scan_response)
        if scan_response.status_code != 200:
            log.error('Get scan status error: {0}'.format(scan_object.get('message', 'N/A')))
            sys.exit(3)

        _scan_complete = False
        scan_status = scan_object.get('status', 0)
        if scan_status == SUCCESS:
            log.info('Scan complete successful')
            _scan_complete = True
        elif scan_status == FAILURE:
            log.error('Scan complete with error')
            _scan_complete = True
        elif scan_status == IN_PROGRESS:
            log.info('Scan in progress...')
        elif scan_status == NOT_STARTED:
            log.info('Scan starting...')
        elif scan_status == STARTED:
            log.info('Scan started')
        elif scan_status == STOPPED:
            log.info('Scan stopped. Analysing phase in progress...')
        else:
            log.error('Get scan status error. Exit with exit code 3')
            sys.exit(3)
        return _scan_complete

    def get_scan_result(self, scan_id):
        """
        Get scan result from specified scan Id. Return all issues with description
        :param scan_id: Scan ID to get results
        :return:
        """
        result_response = self.get('{0}/rest/scanresult/{1}/issues'.format(self.url, scan_id))
        result_object = self._response_json(result_response)
        if result_response.status_code != 200:
            log.error('Get scan result error: {0}'.format(result_object.get('message', 'N/A')))
            return None
        return result_object

    def get_short_stat(self, scan_id):
        """
        Get short issue statistic from specified scan Id
        :param scan_id: Scan ID to get results
        :return:
        """
        result_response = self.get('{0}/rest/scanresult/{1}/issuessummary'.format(self.url, scan_id))
        result_object = self._response_json(result_response)
        if result_response.status_code != 200:
            log.error('Get scan summary error: {0}'.format(result_object.get('message', 'N/A')))
            return {}
        return result_object

    def create_report(self, scan_result):
        """
        Create json report with data specified
        :param scan_result: data to write as Json report
        :return: None
        """
        with open(self.report_path, 'w') as f:
            f.write(json.dumps(scan_result, indent=4))


class Log:
    def info(self, message):
        self._log('INFO', message)

    def error(self, message):
        self._log('ERROR', message)

    def debug(self, message):
        self._log('DEBUG', message)

    def _log(self, level, message):
        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        message = '{time} - {level} {message}'.format(time=current_date, level=level, message=message)
        print(message)


def parse_args():
    parser = argparse.ArgumentParser(description='Start scan and get scan results from Bishop')
    parser.add_argument('--distribution_system', type=str, help='Select how to get apk file', choices=['file', 'hockeyapp'], required=True)

    parser.add_argument('--file_path', type=str, help='Path to local apk file for analyze. This argument required if distribution system set to "file"')
    parser.add_argument('--hockey_token', type=str, help='Auth token for HockeyApp. This argument required if distribution system set to "hockeyapp"')
    parser.add_argument('--bundle_id', type=str, help='Application bundle in HockeyApp. This argument or "--hockey_app_id" required if distribution system set to "hockeyapp"')
    parser.add_argument('--public_id', type=str, help='Application identifier in HockeyApp. This argument required if distribution system set to "hockeyapp"')
    parser.add_argument('--hockey_version', type=str, help='Application version in HockeyApp. If not set - the latest version will be downloaded. This argument required if distribution system set to "hockeyapp"', default='latest')

    parser.add_argument('--bishop_url', type=str, help='Bishop url', required=True)
    parser.add_argument('--token', type=str, help='CI/CD Token for start scan and get results', required=True)
    parser.add_argument('--profile', type=int, help='Project id for scan', required=True)
    parser.add_argument('--testcase', type=int, help='Testcase Id', required=True)

    args = parser.parse_args()

    if args.distribution_system == 'file' and args.file_path is None:
        parser.error('"--distribution_system file" requires "--file_path" argument to be set')
    elif args.distribution_system == 'hockeyapp' and (
            args.hockey_token is None or
            (args.hockey_app is None or args.hockey_app_id is None)):
        parser.error('"--distribution_system hockeyapp" requires "--hockey_token" and "--hockey_app" arguments to be set')

    return args


if __name__ == '__main__':

    log = Log()
    urllib3.disable_warnings()

    arguments = parse_args()

    bishop_url = arguments.bishop_url
    bishop_token = arguments.token
    bishop_profile = arguments.profile
    bishop_testcase_id = arguments.testcase
    distribution_system = arguments.distribution_system

    apk_file = ''
    if distribution_system == 'file':
        apk_file = arguments.file_path
    elif distribution_system == 'hockeyapp':
        hockey_app = HockeyApp(arguments.hockey_token,
                               arguments.bundle_id,
                               arguments.public_id,
                               arguments.hockey_version)
        apk_file = hockey_app.download_app()

    bishop = Bishop(bishop_url, bishop_token, apk_file, bishop_profile, bishop_testcase_id)

    log.info('Start automated scan with test case Id: {0}, profile Id: {1} and file: {2}'.format(
        bishop_testcase_id, bishop_profile, apk_file))

    scan_id = bishop.start_scan()

    if not scan_id:
        log.error('Error when starting scan. Exit with error code 1')
        sys.exit(1)

    scan_complete = False
    log.info('Scan successfully started. Monitor scan status')
    while not scan_complete:
        log.info('Get scan status')
        scan_complete = bishop.get_scan_status(scan_id)
        time.sleep(30)

    log.info('Scan complete, trying to get scan result')
    scan_result = bishop.get_scan_result(scan_id)
    if not scan_result:
        sys.exit(4)

    log.info('Scan complete, analysing issues')
    short_stat = bishop.get_short_stat(scan_id)
    if not short_stat:
        sys.exit(5)
    log.info('Vulnerability details: {0}'.format(short_stat))

    log.info('Creating report...')
    bishop.create_report(scan_result)

    log.info('Job completed successfully')
