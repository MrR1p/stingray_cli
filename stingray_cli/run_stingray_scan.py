import sys
import time
import json
import urllib3
import argparse

from .helpers.const import *
from .helpers.logging import Log
from .distribution_systems.hockey_app import HockeyApp
from .distribution_systems.app_center import AppCenter
from stingray_cli_core import StingrayToken as Stingray



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
    parser.add_argument('--company_id', type=str, help='Company id for starting scan', required=True)
    parser.add_argument('--architecture_id', type=str, help='Architecture id to perform scan', required=True)
    parser.add_argument('--architecture_type', type=str, help='Architecture type (Android or iOS) to perform scan', required=True)
    parser.add_argument('--token', type=str, help='CI/CD Token for start scan and get results', required=True)
    parser.add_argument('--profile', type=int, help='Project id for scan', required=True)
    parser.add_argument('--testcase', type=int, help='Testcase Id')
    parser.add_argument('--report_json_file_name', type=str,  help='Name for the json file with results in structured format')
    parser.add_argument('--nowait', '-nw', action='store_true', help='Wait before scan ends and get results if set to True. If set to False - just start scan and exit')

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


def main():
    urllib3.disable_warnings()

    arguments = parse_args()

    stingray_url = arguments.stingray_url
    stingray_company = arguments.company_id
    stingray_architecture = arguments.architecture_id
    stingray_architecture_type = arguments.architecture_type
    stingray_token = arguments.token
    stingray_profile = arguments.profile
    stingray_testcase_id = arguments.testcase
    stingray_json_file_name = arguments.report_json_file_name
    distribution_system = arguments.distribution_system
    not_wait_scan_end = arguments.nowait

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


    stingray = Stingray(stingray_url, stingray_token, stingray_company)

    Log.info(f'Start automated scan with test case Id: '
             f'{stingray_testcase_id}, profile Id: {stingray_profile} and file: {apk_file}')

    Log.info('Uploading application to server')
    upload_application_resp = stingray.upload_application(apk_file, stingray_architecture_type)
    if not upload_application_resp.status_code == 201:
        Log.error(f'Error while uploading application to server: {upload_application_resp.text}')
        sys.exit(1)

    application = upload_application_resp.json()
    Log.info(f"Application uploaded successfully. Application id: {application['id']}")

    Log.info(f"Create autoscan for application {application['id']}")
    create_dast_resp = stingray.create_auto_scan(profile_id=stingray_profile,
                                                 app_id=application['id'],
                                                 arch_id=stingray_architecture,
                                                 test_case_id=stingray_testcase_id)

    if not create_dast_resp.status_code == 201:
        Log.error(f'Error while creating autoscan: {create_dast_resp.text}')
        sys.exit(1)

    dast = create_dast_resp.json()
    Log.info(f"Autoscan created successfully. Scan id: {dast['id']}")

    if not 'id' in dast and dast.get('id', '') != '':
        Log.error(f'Something went wrong while creating autoscan: {dast}')
        sys.exit(1)

    Log.info(f"Start autoscan with id {dast['id']}")
    start_dast_resp = stingray.start_scan(dast['id'])
    if not start_dast_resp.status_code == 200:
        Log.error(f"Error while starting autoscan with id {dast['id']}: {start_dast_resp.text}")
        sys.exit(1)

    if not_wait_scan_end:
        Log.info('Scan successfully started. Don`t wait for end, exit with zero code')
        sys.exit(0)
    Log.info(f"Autoscan started successfully.")
    Log.info(f"Check scan state with id {dast['id']}")
    get_dast_info_resp = stingray.get_scan_info(dast['id'])
    if not get_dast_info_resp.status_code == 200:
        Log.error(f"Error while getting scan info with id {dast['id']}: {get_dast_info_resp.text}")
        sys.exit(1)

    dast = get_dast_info_resp.json()
    dast_status = dast['state']
    Log.info(f"Current scan status: {DastStateDict.get(dast_status)}")
    count = 0

    Log.info(f"Waiting until scan with id {dast['id']} started.")
    while dast_status in (DastState.CREATED, DastState.STARTING) and count < TRY_COUNT:
        Log.info(f"Try to get scan status for scan id {dast['id']}. Count number {count}")
        get_dast_info_resp = stingray.get_scan_info(dast['id'])
        if not get_dast_info_resp.status_code == 200:
            Log.error(f"Error while getting scan info with id {dast['id']}: {get_dast_info_resp.text}")
            sys.exit(1)

        dast = get_dast_info_resp.json()
        dast_status = dast['state']
        Log.info(f"Current scan status: {DastStateDict.get(dast_status)}")
        count += 1
        Log.info(f"Wait {SLEEP_TIMEOUT} seconds and try again")
        time.sleep(SLEEP_TIMEOUT)

    if not dast['state'] in (DastState.STARTED, DastState.ANALYZING, DastState.SUCCESS):
        Log.error(f"Error with scan id {dast['id']}. Current scan status: {dast['state']},"
                  f" but expected to be {DastState.STARTED}, {DastState.ANALYZING} or {DastState.SUCCESS}")
        sys.exit(1)
    Log.info(f"Scan with {dast['id']} finished and now analyzing. Wait until analyzing stage is finished.")

    Log.info(f"Waiting until scan with id {dast['id']} finished.")
    get_dast_info_resp = stingray.get_scan_info(dast['id'])
    if not get_dast_info_resp.status_code == 200:
        Log.error(f"Error while getting scan info with id {dast['id']}: {get_dast_info_resp.text}")
        sys.exit(1)
    dast = get_dast_info_resp.json()
    dast_status = dast['state']
    Log.info(f"Current scan status: {DastStateDict.get(dast_status)}")
    count = 0

    while dast_status in (DastState.STARTED, DastState.ANALYZING) and count < TRY_COUNT:
        Log.info(f"Try to get scan status for scan id {dast['id']}. Count number {count}")
        get_dast_info_resp = stingray.get_scan_info(dast['id'])
        if not get_dast_info_resp.status_code == 200:
            Log.error(f"Error while getting scan info with id {dast['id']}: {get_dast_info_resp.text}")
            sys.exit(1)
        dast = get_dast_info_resp.json()
        dast_status = dast['state']
        Log.info(f"Current scan status: {DastStateDict.get(dast_status)}")
        count += 1
        Log.info(f"Wait {SLEEP_TIMEOUT} seconds and try again")
        time.sleep(SLEEP_TIMEOUT)

    Log.info(f"Check is scan with id {dast['id']} finished correctly.")
    get_dast_info_resp = stingray.get_scan_info(dast['id'])
    if not get_dast_info_resp.status_code == 200:
        Log.error(f"Error while getting scan info with id {dast['id']}: {get_dast_info_resp.text}")
        sys.exit(1)
    dast = get_dast_info_resp.json()

    if not dast['state'] == DastState.SUCCESS:
        Log.error(f"Expected state {DastStateDict.get(DastState.SUCCESS)}, but in real it was {dast['state']}. Exit with error status code.")
        sys.exit(1)

    Log.info(f"Create and download report for scan with id {dast['id']}.")
    report_path = f"./scan-report-{dast['id']}.pdf"
    report = stingray.download_report(dast['id'])
    if report.status_code != 200:
        Log.error(f"Report creating failed with error {report.text}. Exit...")
        sys.exit(1)

    with open(report_path, 'wb') as f:
        f.write(report.content)
    Log.info(f"Report for scan {dast['id']} successfully created and available at path: {report_path}.")

    if stingray_json_file_name:
        Log.info(f"Create and download JSON report for scan with id {dast['id']} to file {stingray_json_file_name}.")
        json_report = stingray.get_scan_issues(dast['id'])
        if json_report.status_code != 200:
            Log.error(f"JSON report creating failed with error {report.text}. Exit...")
            sys.exit(1)

        Log.info(f"Saving json results to file {stingray_json_file_name}.")
        stingray_json_file = stingray_json_file_name if stingray_json_file_name.endswith('.json') else f'{stingray_json_file_name}.json'
        with open(stingray_json_file, 'w') as fp:
            json.dump(json_report, fp, indent=4)

    Log.info(f"JSON report for scan {dast['id']} successfully created and available at path: {json_report}.")

    Log.info('Job completed successfully')

if __name__ == '__main__':
    main()