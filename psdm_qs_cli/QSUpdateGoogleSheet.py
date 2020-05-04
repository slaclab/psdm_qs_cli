#!/usr/bin/env python
'''Use the questionnaire client to update the specified Google sheet.
We take a list of attributes in a file, (names with mappings) and generate a row per proposal and a column per attribute.
'''
import os
import argparse
import json
import logging
import itertools

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



    # Find column names from spreadsheet
    name2ColumnId = { x[1].lower() : x[0] for x in enumerate(sheet.values().get(spreadsheetId=google_sheet_id,range="Sheet1!1:1").execute().get('values', [])[0]) }
    attr2ColumnRef = { x[0] : __col_to_A1__(name2ColumnId[x[1].lower()]) for x in column2Names if  x[1].lower() in name2ColumnId }
    # Start from row 2; the first proposal ID comes into A5.
    firstRowForProposals = "2"

    cranges = []
    for c in attr2ColumnRef.values():
        cranges.append("Sheet1!" + c + firstRowForProposals + ":" + c)

    logger.debug(sheet.values())
    sheet.values().batchClear(spreadsheetId=google_sheet_id, body={ "ranges": cranges }).execute()

    proposals = qs.getProposalsListForRun(run)
    rowNum = 1
    for proposalid in sorted(proposals.keys()):
        print("Getting details for proposal ", proposalid)
        proposalDetails = qs.getProposalDetailsForRun(run, proposalid)
        # Add the details of each proposal to the information obtained from the proposal list call.
        proposals[proposalid].update(proposalDetails)

    update_data = []
    for attr, cref in attr2ColumnRef.items():
        pvals = []
        for proposalid in sorted(proposals.keys()):
            if attr in proposals[proposalid]:
                pvals.append(proposals[proposalid][attr])
            else:
                pvals.append("")
        update_data.append({
            "range": "Sheet1!" + cref + firstRowForProposals + ":" + cref,
            "majorDimension": "COLUMNS",
            "values": [ pvals ]
        })

    body = {
        "valueInputOption": "USER_ENTERED",
        "data": update_data,
        "includeValuesInResponse": True
    }

    sheet.values().batchUpdate(spreadsheetId=google_sheet_id, body=body).execute()

def __col_to_A1__(col):
    """
    Convert a zero indexed column cell reference to a string in the A1 notation.
    From https://github.com/jmcnamara/XlsxWriter/blob/master/xlsxwriter/utility.py
    """
    col_num = col
    if col_num < 0:
        raise Exception("Col number %d must be >= 0" % col_num)

    col_num += 1  # Change to 1-index.
    col_str = ''

    while col_num:
        remainder = col_num % 26
        if remainder == 0:
            remainder = 26
        col_letter = chr(ord('A') + remainder - 1)
        col_str = col_letter + col_str
        col_num = int((col_num - 1) / 26)
    return col_str


def main():
    parser = argparse.ArgumentParser(description='Load data from the questionnaire into a an Excel spreadsheet')
    parser.add_argument('--questionnaire_url', default="https://pswww.slac.stanford.edu/ws-kerb/questionnaire/")
    parser.add_argument('--no_kerberos', action="store_false")
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--spreadsheetid', default=SAMPLE_SPREADSHEET_ID)
    parser.add_argument('run')
    parser.add_argument('attributes_file', help='A JSON file with an array of dicts; each of which has a attrname and a label.')
    args = parser.parse_args()

    updateGoogleSheetForRun(args.run, args.attributes_file, args.spreadsheetid, questionnaire_url=args.questionnaire_url, no_kerberos=args.no_kerberos, user=args.user, password=args.password)


if __name__ == '__main__':
    main()
