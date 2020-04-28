#!/usr/bin/env python
'''Use the questionnaire client to update the specified Google sheet.
We take a list of attributes in a file, (names with mappings) and generate a row per proposal and a column per attribute.
'''
import os
import argparse
import json
import logging

from googleapiclient.discovery import build
from google.oauth2 import service_account

from psdm_qs_cli import QuestionnaireClient

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '123shYBqhQCiUVSb5lCMBv8Mx3ziuEkJ-P8E92UuJyeY'


def updateGoogleSheetForRun(run, attributes_file, google_sheet_id, questionnaire_url="https://pswww.slac.stanford.edu/ws-kerb/questionnaire/", no_kerberos=False, user=None, password=None):
    '''
    Update the specified google sheet with the attributes for the run.
    :param: qs - A Questionnaire client
    :run: The number number/name; this is a string like run15 which is what the questionnaire uses in its URL
    '''
    qs = QuestionnaireClient(questionnaire_url, no_kerberos, user=user, pw=password)

    column2Names = [('proposal_id', "Proposal")]
    with open(attributes_file, 'r') as f:
        attrs = json.load(f)
        column2Names.extend((x["attr"], x["label"]) for x in attrs)

    credentials = service_account.Credentials.from_service_account_file(os.environ["CREDENTIALS_JSON"])
    scoped_credentials = credentials.with_scopes( SCOPES )
    service = build('sheets', 'v4', credentials=scoped_credentials, cache_discovery=False)

    # Call the Sheets API
    sheet = service.spreadsheets()
    sheet.values().clear(spreadsheetId=SAMPLE_SPREADSHEET_ID,range="Sheet1").execute()

    values = []
    values.append([ x[1] for x in column2Names ])

    proposals = qs.getProposalsListForRun(run)
    rowNum = 1
    for proposalid in sorted(proposals.keys()):
        print("Getting details for proposal ", proposalid)
        proposalDetails = qs.getProposalDetailsForRun(run, proposalid)
        # Add the details of each proposal to the information obtained from the proposal list call.
        proposals[proposalid].update(proposalDetails)
        pvals = []
        for clnum in range(len(column2Names)):
            ckey = column2Names[clnum][0]
            if ckey in proposals[proposalid]:
                pvals.append(proposals[proposalid][ckey])
            else:
                pvals.append("")
        values.append(pvals)

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": [ {
            "range": "Sheet1",
            "majorDimension": "ROWS",
            "values": values } ],
        "includeValuesInResponse": True
    }

    sheet.values().batchUpdate(spreadsheetId=SAMPLE_SPREADSHEET_ID, body=body).execute()

def main():
    parser = argparse.ArgumentParser(description='Load data from the questionnaire into a an Excel spreadsheet')
    parser.add_argument('--questionnaire_url', default="https://pswww.slac.stanford.edu/ws-kerb/questionnaire/")
    parser.add_argument('--no_kerberos', action="store_false")
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('run')
    parser.add_argument('attributes_file', help='A JSON file with an array of dicts; each of which has a attrname and a label.')
    args = parser.parse_args()

    updateGoogleSheetForRun(args.run, args.attributes_file, SAMPLE_SPREADSHEET_ID, questionnaire_url=args.questionnaire_url, no_kerberos=args.no_kerberos, user=args.user, password=args.password)


if __name__ == '__main__':
    main()
