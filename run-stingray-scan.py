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


class AppCenter(DistributionSystem):
    """
    Downloading application from HockeyApp distribution system
    """
    url = 'https://api.appcenter.ms/v0.1'
    download_path = 'downloaded_apps'

    def __init__(self, token, app_name, owner_name, version, id):
        super().__init__(app_name, version)

        self.id = id
        self.owner_name = owner_name
        self.auth_header = {'X-API-Token': token}

    def get_version_info_by_id(self):
        log.info('AppCenter - Get information about application')
        url = '{0}/apps/{1}/{2}/releases/{3}'.format(self.url, self.owner_name, self.app_identifier, self.id)
        response = requests.get(url, headers=self.auth_header)
        if response.status_code != 200:
            log.error(
                'AppCenter - Failed to get information about application release. Request return status code: {0}'.format(
                    response.status_code))
            sys.exit(4)

        version_info = response.json()
        return version_info

    def get_version_info_by_version(self):
        url = '{0}/apps/{1}/{2}/releases?scope=tester'.format(self.url, self.owner_name, self.app_identifier)

        response = requests.get(url, headers=self.auth_header)
        if response.status_code != 200:
            log.error(
                'AppCenter - Failed to get information about application releases. Request return status code: {0}'.format(
                    response.status_code))
            sys.exit(4)

        versions_info = response.json()
        for version in versions_info:
            if version['version'] != self.app_version:
                continue

            self.id = version['id']
            version_info = self.get_version_info_by_id()
            return version_info

        return None

    def download_app(self):
        if self.id:
            version_info = self.get_version_info_by_id()
        else:
            version_info = self.get_version_info_by_version()

        if not version_info:
            log.error('AppCenter - Failed to get app version information. Verify that you set up arguments correctly and try again')

        log.info('AppCenter - Start download application')
        download_url = version_info.get('download_url')

        response = requests.get(download_url, headers=self.auth_header, allow_redirects=True)
        if response.status_code != 200:
            log.error('AppCenter - Failed to download application. Request return status code: {0}'.format(
                response.status_code))
            sys.exit(4)

        file_name = '{0}-{1}.apk'.format(self.app_identifier, version_info['version'])
        path_to_save = os.path.join(self.download_path, file_name)

        if not os.path.exists(self.download_path):
            os.mkdir(self.download_path)

        with open(path_to_save, 'wb') as file:
            file.write(response.content)

        log.info('AppCenter - Download application successfully completed to {0}'.format(path_to_save))

        return path_to_save



class Stingray:
    """
    Class for interact with Stingray system through REST API
    """
    def __init__(self, base_url, token, file, profile, testcase):
        # self.report_path = 'stingray_scan_report.json'
        self.headers = {'Access-token': token}
        self.url = base_url
        self.apk_file = file
        self.profile = profile
        self.testcase = testcase

    def get(self, url):
        """
        Get method for Stingray REST API.
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
        Start automated scan through REST API
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

        # remove it when the correct responses will be provided by api in that case
        if scan_response.status_code == 500:
            log.error('Please check the correctness of the provided testcase id')
        # remove it when the correct responses will be provided by api in that case
        if scan_response.status_code == 401:
            log.error('Please check the correctness of the provided profile id')

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

    def create_report(self, scan_result, type):
        """
        Create json report with data specified
        :param scan_result: data to write as Json report
        :return: None
        """
        if type == 'standard' or type == 'grouping':
            report_name = 'stingray_scan_{0}_report.json'.format(type)
        else:
            report_name = 'stingray_scan_report-testcase_{}.json'.format(self.testcase)
        with open(report_name, 'w') as f:
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

class ValidateReport(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        valid_types = ('standard', 'separate', 'grouping')
        reportType = values
        for i in reportType:
            if i not in valid_types:
                raise ValueError('invalid type {0}, supported types are {1}'.format(i, valid_types))
        setattr(args, self.dest, reportType)

def parse_args():
    parser = argparse.ArgumentParser(description='Start scan and get scan results from Stingray')
    parser.add_argument('--distribution_system', type=str, help='Select how to get apk file', choices=['file', 'hockeyapp', 'appcenter'], required=True)

    # Arguments used for distribution_system = file
    parser.add_argument('--file_path', type=str, help='Path to local apk file for analyze. This argument required if distribution system set to "file"')

    # Arguments used for distribution_system = hockeyapp
    parser.add_argument('--hockey_token', type=str, help='Auth token for HockeyApp. This argument required if distribution system set to "hockeyapp"')
    parser.add_argument('--hockey_bundle_id', type=str, help='Application bundle in HockeyApp. This argument or "--hockey_public_id" required if distribution system set to "hockeyapp"')
    parser.add_argument('--hockey_public_id', type=str, help='Application identifier in HockeyApp. This argument or "--hockey_bundle_id" required if distribution system set to "hockeyapp"')
    parser.add_argument('--hockey_version', type=str, help='Application version in HockeyApp. If not set - the latest version will be downloaded. This argument required if distribution system set to "hockeyapp"', default='latest')

    # Arguments used for distribution_system = appcenter
    parser.add_argument('--appcenter_token', type=str, help='Auth token for AppCenter. This argument required if distribution system set to "appcenter"')
    parser.add_argument('--appcenter_owner_name', type=str, help='Application owner name in AppCenter. This argument required if distribution system set to "appcenter"')
    parser.add_argument('--appcenter_app_name', type=str, help='Application name in AppCenter. This argument required if distribution system set to "appcenter"')
    parser.add_argument('--appcenter_release_id', type=str, help='Release id in AppCenter. If not set - the latest release will be downloaded. This argument or "--ac_app_version" required if distribution system set to "appcenter"')
    parser.add_argument('--appcenter_app_version', type=str,help='Application version in AppCenter. This argument  or "--appcenter_release_id" required if distribution system set to "appcenter"')

    # Arguments for Stingray
    parser.add_argument('--stingray_url', type=str, help='Stingray url', required=True)
    parser.add_argument('--token', type=str, help='CI/CD Token for start scan and get results', required=True)
    parser.add_argument('--profile', type=int, help='Project id for scan', required=True)
    parser.add_argument('--testcase', nargs='+', type=int, help='Testcase Id')
    parser.add_argument('--report', nargs='*', type=str, help='Select which type of report should be created', action=ValidateReport, default=['standard'])

    args = parser.parse_args()

    if args.distribution_system == 'file' and args.file_path is None:
        parser.error('"--distribution_system file" requires "--file_path" argument to be set')
    elif args.distribution_system == 'hockeyapp' and (
            args.hockey_token is None or
            (args.hockey_bundle_id is None or args.hockey_public_id is None)):
        parser.error('"--distribution_system hockeyapp" requires "--hockey_token" and "--hockey_app" arguments to be set')
    elif args.distribution_system == 'appcenter' and (
        args.appcenter_token is None or args.appcenter_owner_name is None or args.appcenter_app_name is None or (
        args.appcenter_release_id is None and args.appcenter_app_version is None)):
        parser.error(
            '"--distribution_system appcenter" requires "--appcenter_token", "--appcenter_owner_name",  "--appcenter_app_name" and '
            '"--appcenter_release_id" or "--appcenter_app_version" arguments to be set')
    return args

def join_results(scans, type):
    '''
    Get scan results from several tescases and join them in one common result
    '''

    report = []
    added = False

    # Grouping of scan results, issues of a same type are joined together, these issues details go to a list
    if type == 'grouping':

        for scan in scans:
            for issue in scan:

                if not report:
                    report.append(scan[0])
                    continue

                for addedIssue in report:

                    added = False
                    if issue['name'] == addedIssue['name']:

                        if issue['details'] != addedIssue['details'] and issue['details'] not in addedIssue['details']:
                            if not isinstance(addedIssue['details'][0], list):
                                temp=[]
                                temp.append(addedIssue['details'])
                                temp.append(issue['details'])
                                addedIssue['details'] = temp
                            else:
                                addedIssue['details'].append(issue['details'])

                        added = True
                        addedIssue['id'].extend(issue['id'])
                        if issue['scan_id'][0] not in addedIssue['scan_id']:
                            addedIssue['scan_id'].extend(issue['scan_id'])
                        break

                if not added:
                    report.append(issue)
    #Standard report, same issues from different testcases are joined to escape duplicates
    else:
        for scan in scans:

            if not report:
                report.extend(scan)
                continue
            currReportLen = len(report)

            for issue in scan:

                ind = 0
                added= False

                for addedIssue in report:

                    ind += 1
                    if issue['name'] == addedIssue['name'] and issue['details'] == addedIssue['details']:
                        addedIssue['id'].extend(issue['id'])
                        if issue['scan_id'][0] not in addedIssue['scan_id']:
                            addedIssue['scan_id'].extend(issue['scan_id'])
                        added = True
                        break

                    if ind == currReportLen and not added:
                        report.append(issue)
                        break
    return(report)

if __name__ == '__main__':

    log = Log()
    urllib3.disable_warnings()

    arguments = parse_args()
    results = []

    stingray_url = arguments.stingray_url
    stingray_token = arguments.token
    stingray_profile = arguments.profile
    stingray_testcase_set = set(arguments.testcase)
    distribution_system = arguments.distribution_system

    report_types = arguments.report
    if not report_types:
        report_types = ['standard']

    apk_file = ''
    if distribution_system == 'file':
        apk_file = arguments.file_path
    elif distribution_system == 'hockeyapp':
        hockey_app = HockeyApp(arguments.hockey_token,
                               arguments.hockey_bundle_id,
                               arguments.hockey_public_id,
                               arguments.hockey_version)
        apk_file = hockey_app.download_app()
    elif distribution_system == 'appcenter':
        appcenter = AppCenter(arguments.appcenter_token,
                              arguments.appcenter_app_name,
                              arguments.appcenter_owner_name,
                              arguments.appcenter_app_version,
                              arguments.appcenter_release_id)
        apk_file = appcenter.download_app()

    for stingray_testcase_id in stingray_testcase_set:

        if len(stingray_testcase_set) > 1:
            log.info('Processing testcase {0}'.format(stingray_testcase_id))
        else:
            if 'standard' in report_types:
                report_types.remove('standard')
            if not report_types:
                report_types = ['separate']

        stingray = Stingray(stingray_url, stingray_token, apk_file, stingray_profile, stingray_testcase_id)

        log.info('Start automated scan with test case Id: {0}, profile Id: {1} and file: {2}'.format(
            stingray_testcase_id, stingray_profile, apk_file))

        scan_id = stingray.start_scan()

        if not scan_id:
            log.error('Error when starting scan. Exit with error code 1')
            sys.exit(1)

        scan_complete = False
        log.info('Scan successfully started. Monitor scan status')
        while not scan_complete:
            log.info('Get scan status')
            scan_complete = stingray.get_scan_status(scan_id)
            time.sleep(30)

        log.info('Scan complete, trying to get scan result')
        scan_result = stingray.get_scan_result(scan_id)
        if not scan_result:
            continue

        log.info('Scan complete, analysing issues')
        short_stat = stingray.get_short_stat(scan_id)
        if not short_stat:
            sys.exit(5)
        log.info('Vulnerability details: {0}'.format(short_stat))

        for i in scan_result:
            i['id'] = str(stingray_testcase_id) + '-' + str(i['id'])#add testcase to id
            i['scan_id'] = scan_id

        if 'separate' in report_types:
            stingray.create_report(scan_result, type)
            log.info('Creating separate report...')

        for i in scan_result:
            i['id'] = [i['id']]
            i['scan_id'] = [i['scan_id']]

        results.append(scan_result)

    for type in report_types:
        if type == 'standard' or type == 'grouping':
            common_result = join_results(results, type)
            log.info('Creating {0} report...'.format(type))
            stingray.create_report(common_result, type)

    if len(results) == 0:
        log.info('There is no issue data for the report')
    
    log.info('Job completed successfully')
