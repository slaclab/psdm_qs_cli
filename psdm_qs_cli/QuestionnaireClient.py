#!/usr/bin/env python
'''
Various web service calls to the Questionnaire backend to get data for reporting.
'''
import json
import requests
import datetime
import logging
import getpass
from functools import partial

from six.moves.urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    from krtc import KerberosTicket
except ImportError:
    KerberosTicket = None
    logger.warning('krtc not installed: Kerberos ticket-based authentication '
                   'unavailable.')


class QuestionnaireClient:
    """
    Interface to the LCLS Questionnaire

    Parameters
    ----------
    url: str, optional
        Provide a base URL for the Questionnaire. If left as None the
        appropriate URL will be chosen based on your authentication method

    use_kerberos: bool, optional
        Use a Kerberos ticket to login to the Questionnaire. This is the
        default authentication method

    user: str, optional
        A username for ws_auth sign-in. If not provided the current login name
        is used
    pw = str, optional
        A password for ws_auth sign-in. If not provided a password will be
        requested
    """
    kerb_url = 'https://pswww.slac.stanford.edu/ws-kerb/questionnaire/'
    wsauth_url = "https://pswww.slac.stanford.edu/ws-auth/questionnaire/"

    def __init__(self, url=None, use_kerberos=True, user=None, pw=None):
        if use_kerberos:
            if KerberosTicket is None:
                raise RuntimeError('Kerberos-based authentication unavailable.  '
                                   'Please install krtc.')

            self.questionnaire_url = url or self.kerb_url
            self.krbheaders = KerberosTicket("HTTP@" + urlparse(self.questionnaire_url).hostname).getAuthHeaders()
            self.rget = partial(requests.get, headers=self.krbheaders)
            self.rpost = partial(requests.post, headers=self.krbheaders)
        else:
            self.questionnaire_url = url or self.wsauth_url
            # Find the login information if not provided
            user = user or getpass.getuser()
            pw = pw or getpass.getpass()
            self.auth = requests.auth.HTTPBasicAuth(user, pw)
            self.rget = partial(requests.get, auth=self.auth)
            self.rpost = partial(requests.post, auth=self.auth)

    def getEnumerations(self, run):
        """
        Get the enumerations in a run period.
        This returns a list of proposal value names that are comboboxes.
        :param: run - a run period (for example, run16)
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/" + run + "/get_enum_field_names")
        if r.status_code <= 299:
            return r.json()
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)

    def getProposalsListForRun(self, run):
        """
        Get a list of proposals for a run period.
        :param: run - a run period (for example, run16)
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/experiments/" + run)
        if r.status_code <= 299:
            experiments = r.json()
            # experiments is a list of dicts with instrument and proposal_id
            proposals = {}
            for experiment in experiments["experiments"]:
                proposals[experiment['proposal_id']] = {'Instrument': experiment['instrument'], 'proposal_id': experiment['proposal_id']}
            return proposals
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)

    def _updateIfExists(self, ret, srcdata, srcField, destName):
        '''Update ret if and only if the sequence of fields exists in the src data
        :param: ret - The return dict to update
        :param: srcdata - The source data as a dict
        :param: srcField - The srcField in canonical format - for example, contacts.point_of_contact
        :param: destName - The name of the field in ret. So we can take contacts.point_of_contact and create a POC field..
        '''
        data = srcdata
        for field in srcField.split("."):
            if field not in data:
                return
            else:
                data =  data[field]
        ret[destName] = data


    def getProposalDetailsForRun(self, run, proposalid):
        """
        Get the detailed list of key value pairs for a proposal in a run period
        :param: run - a run period (for example, run16)
        :param: proposalid - the proposal id, (for example, LR01)
        """
        ret = {}
        ret['proposal_id'] = proposalid
        ret['Proposal'] = proposalid
        r = self.rget(self.questionnaire_url + "ws/proposal/attribute/" + run + "/" + proposalid)
        if r.status_code <= 299:
            proposalData = r.json()
            # proposalData is a dict with list of dicts for the values
            # We want the id and the val for the final dicts.
            ret.update({x['id'] : x['val'] for x in [item for sublist in proposalData.values() for item in sublist]})
            # Generate Beryllium lens summaries for Daniel
            hzvr = {'vertical': 'VERT', 'horizontal' : 'HORZ'}
            for belocid, repid in {"hutch-be-top-d": "Be-TOP",  "hutch-be-mid-d": "Be-MID", "hutch-be-bot-d": "Be-BTM", "hutch-be-sam-d": "Be-AIR"}.items():
                tpls = sorted([(c['id'].split("-")[3].replace("d1", "1D").replace("d2", "2D"), c['id'].split("-")[4], "x", c['val']) for c in proposalData.get('hutch', []) if c['id'].startswith(belocid) and int(c['val'])], key=lambda x : (x[0], int(x[1])))
                if tpls:
                    h_or_v = "".join([hzvr.get(x['val'], 'VERT/HORZ') for x in proposalData['hutch'] if x['id'] == belocid.replace("-d", "-orientation")])
                    tpls = [x + (h_or_v,) if x[0]=='1D' else x for x in tpls]
                    ret[repid] = "  ".join(("".join(_) for _ in tpls))
            combined_be = "\n".join(["{}:{}".format(fnl_be_attr, ret[fnl_be_attr]) for fnl_be_attr in ["Be-TOP", "Be-MID", "Be-BTM", "Be-AIR"] if fnl_be_attr in ret])
            if combined_be:
                ret["Be-All Beryllium Lens Stack Recipes"] = combined_be
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)
        r = self.rget(self.questionnaire_url + "ws/questionnaire/urawidata/" + run + "/" + proposalid)
        if r.status_code <= 299:
            urawiData = r.json()
            if urawiData['info']['startDate']:
                ret.update({'StartDate': urawiData['info']['startDate']})
            if urawiData['info']['stopDate']:
                ret.update({'EndDate': urawiData['info']['stopDate']})
            self._updateIfExists(ret, urawiData, "contacts.point_of_contact", "urawi_poc")
            if 'personnel-poc-sci1' in ret:
                ret["POC"] = ret['personnel-poc-sci1']
            self._updateIfExists(ret, urawiData, "info.proposalTitle", "title")
            self._updateIfExists(ret, urawiData, "info.proposalAbstract", "abstract")
            self._updateIfExists(ret, urawiData, "info.spokesPerson.firstName", "Spokesperson First")
            self._updateIfExists(ret, urawiData, "info.spokesPerson.lastName", "Spokesperson Last")
            self._updateIfExists(ret, urawiData, "info.spokesPerson.email", "Spokesperson Email")
            self._updateIfExists(ret, urawiData, "info.nonURAWI_proposal", "nonURAWI_proposal")
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)
        return ret

    def formLabelMappings(self, run):
        '''
        The form definitions can include optional reporting labels.
        This call generates a dict with the mapping between the attribute value name and the reporting label if one exists.
        This is also the process used to map multiple values into and array under a single reporting label.
        For example, xraytech-tech-1, xraytech-tech-2 etc will be mapped to "X-ray Techniques" as an array
        '''
        nameMappings = {}
        tabNames = self.rget(self.questionnaire_url + "ws/questionnaire/" + run + "/tabnames").json()
        for formTabName in tabNames:
            logger.info("Getting form data for %s", formTabName)
            r = self.rget(self.questionnaire_url + "ws/questionnaire/" + run + "/form_data_definitions?form_name=" + formTabName)
            if r.status_code <= 299:
                formDefinitions = r.json()
                for formDefinition in formDefinitions:
                    if 'reporting_label' in formDefinition:
                        nameMappings[formDefinition['attribute_id']] = formDefinition['reporting_label']
                    else:
                        if 'quantity' in  formDefinition and int(formDefinition['quantity']) > 1:
                            nameMappings[formDefinition['attribute_id']] = formDefinition['attribute_id'][:(formDefinition['attribute_id'].rfind("_")-1)]
            else:
                raise Exception("Invalid HTTP status code from server", r.status_code)
        return nameMappings

    def getProposalsStatusForRun(self, run):
        """
        Get the changes made for a proposal in a run period; we get a list of who made what change when.
        :param: run - a run period (for example, run16)
        :param: proposalid - the proposal id, (for example, LR01)
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/proposals_status/" + run)
        if r.status_code <= 299:
            return r.json()['experiment_status']
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)

    def getProposalsPersonnelForRun(self, run):
        """
        Get personnel for all the proposals in a run period.
        This is a special SLAC only tab containing the list of personnel for a proposal.
        :param: run - a run period (for example, run16)
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/proposals_personnel/" + run)
        now = datetime.datetime.now()
        if r.status_code <= 299:
            datas = r.json()['proposals_personnel']
            for data in datas:
                if data['startDate'] and data['endDate']:
                    stdate  = datetime.datetime.strptime(data['startDate'], '%Y-%m-%d %H:%M:%S')
                    enddate = datetime.datetime.strptime(data['endDate'],   '%Y-%m-%d %H:%M:%S')
                    data['daysToStart'] = (stdate  - now).days
                    data['daysToEnd']   = (enddate - now).days
                    logger.debug("Start date %s End date %s daysToStart %s daysToEnd %s", data['startDate'], data['endDate'], data['daysToStart'], data['daysToEnd'])
                else:
                    data['daysToStart'] = 0
                    data['daysToEnd']   = 0
            return datas
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)


    def getExpName2URAWIProposalIDs(self):
        """
        Get the best guess for experiment name to URAWI proposal IDs.
        Returns a dict of experiment name (xppi0915) to URAWI proposal ID (LI09).
        The experiment name is what is used with the elog; the URAWI proposal ID is what is used with the questionnaire.
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/getURAWIProposalIds")
        if r.status_code <= 299:
            return r.json()
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)

    def lookupByExperimentName(self, experiment_name):
        """
        Given an experiment name, try to get the best guess as to the proposal_id and run period.
        """
        r = self.rget(self.questionnaire_url + "ws/questionnaire/lookupByExperimentName", { "experiment_name": experiment_name } )
        if r.status_code <= 299:
            return r.json()
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)


    def updateProposalAttribute(self, run, proposal_id, attrname, attrvalue):
        """
        Updates the attribute specified by attrname to the value specified by attrvalue for the
        proposal specified by proposal_id in the specified run.
        Writes to the questionnaire do require authentication/authorization; so it's best to use Kerberos for this.
        For example, qscli.updateProposalAttribute("run17", "LR63", "pcdssetup-motors-setup-1-purpose", "Value of purpose")
        """
        r = self.rpost(self.questionnaire_url + "ws/proposal/attribute/" + run + "/" + proposal_id, data={'run_id': run, 'id': attrname, 'val': attrvalue})
        if r.status_code <= 299:
            return r.json()
        else:
            raise Exception("Invalid HTTP status code from server", r.status_code)
