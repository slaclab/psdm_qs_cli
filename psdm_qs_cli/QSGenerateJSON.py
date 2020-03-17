#!/usr/bin/env python
'''Use the questionnaire client to save all the data locally to a JSON document
'''

import argparse
import json

from psdm_qs_cli import QuestionnaireClient


def generateJSONDocumentForRun(qs, run, useLabels, jsonFilePath):
    '''
    Generate a JSON document with data from a run.
    :param: qs - A Questionnaire client
    :run: The number number/name; this is a string like run15 which is what the questionnaire uses in its URL
    :useLabels: - Use the labels as the attribute names.
    '''

    nameMappings = qs.formLabelMappings(run)

    # Get a list of proposals
    proposals = qs.getProposalsListForRun(run)
    for proposalid in proposals.keys():
        print("Getting details for proposal ", proposalid)
        proposalDetails = qs.getProposalDetailsForRun(run, proposalid)
        # Add the details of each proposal to the information obtained from the proposal list call.
        if useLabels:
            mappedProposalDetails = {}
            for k, v in proposalDetails.items():
                if k in nameMappings:
                    mappedProposalDetails[nameMappings[k]] = v
                else:
                    mappedProposalDetails[k] = v
                proposals[proposalid].update(mappedProposalDetails)
        else:
            proposals[proposalid].update(proposalDetails)

    with open(jsonFilePath, 'w') as f:
        json.dump(proposals, f)
    print("Saved data into", jsonFilePath)


def main():
    parser = argparse.ArgumentParser(description='Load data from the questionnaire into a an Excel spreadsheet')
    parser.add_argument('--questionnaire_url', default="https://pswww.slac.stanford.edu/ws-kerb/questionnaire")
    parser.add_argument('--useLabels', action="store_true", help="Use the questionnaire labels as the attribute names.")
    parser.add_argument('--no_kerberos', action="store_false")
    parser.add_argument('run')
    parser.add_argument('jsonFilePath')
    args = parser.parse_args()

    qs = QuestionnaireClient(args.questionnaire_url, args.no_kerberos)
    generateJSONDocumentForRun(qs, args.run, args.useLabels, args.jsonFilePath)


if __name__ == '__main__':
    main()
