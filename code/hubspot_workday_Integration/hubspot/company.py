import json

import requests
import unicodecsv as csv

from hubspot.authorization import hs_autho
from modules.database import db
from modules.log import logger
from workday.customer import Customer

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Company:
    attributes = ["id", "name", "description"]
    def __init__(self, company_dic):
        self.__dict__ = company_dic

    @classmethod
    def from_hubspot(cls, objectId):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}
        r = requests.get("https://api.hubapi.com/companies/v2/companies/" + str(objectId), headers=headers)

        while r.status_code == 401: # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("https://api.hubapi.com/companies/v2/companies/" + str(objectId), headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_COMPANY %s\n %s\n\n" % (r.status_code, r.content))
            print "RESPONSE HUBSPOT GET_COMPANY %s" % r.status_code
            return

        print "company from hs " + str(r.status_code)
        result = json.loads(r.content)

        company_dic = {}
        company_dic["id"] = str(result["companyId"])

        company_dic.update({k: v.get("value") for k, v in result.get("properties", {}).items()})

        return cls(company_dic)



    @staticmethod
    def get_all_companies_old(offset="", properties=None, propertiesWithHistory=False):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        properties = reduce(lambda x, y: x+y, ["&properties=%s"%x for x in p])
        offset_parameter = ""
        if offset:
            offset_parameter = "&offset=%s" % offset
        parameters = properties + offset_parameter
        r = requests.get("https://api.hubapi.com/companies/v2/companies/paged?includeAssociations=true&limit=250" + parameters, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("https://api.hubapi.com/companies/v2/companies/paged?includeAssociations=true&limit=250" + parameters, headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_COMPANIES %s\n %s\n\n" % (r.status_code, r.content))
        return r

    @classmethod
    def get_all_companies(cls, properties=None, propertiesWithHistory=False):
        if not properties:
            properties = cls.attributes

        companies = []
        offset = ""
        while True:
            r = Company.get_page_companies(offset, properties, propertiesWithHistory)
            result = json.loads(r.content)
            offset = result["offset"]

            for c in result["companies"]:
                companies.append(c)
            if not result["has-more"]:
                break

        return companies

    @staticmethod
    def get_page_companies(offset, properties, propertiesWithHistory=False, limit="250"):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        # properties_params = reduce(lambda x, y: x+y, ["&properties=%s" % x for x in properties])
        params = []
        params += ["limit=%s" % limit]
        if propertiesWithHistory:
            params += ["propertiesWithHistory=%s" % x for x in properties]
        else:
            params += ["properties=%s" % x for x in properties]
        if offset:
            params += ["offset=%s" % offset]
        url = "https://api.hubapi.com/companies/v2/companies/paged?" + "&".join(params)
        r = requests.get(url, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_PAGE_COMPANIES %s\n %s\n\n" % (r.status_code, r.content))
        return r

    @staticmethod
    def export_all_companies_old(filename):
        with open(filename, 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            spamwriter.writerow(("companyid", "companyname"))
            offset = ""
            while True:
                r = Company.get_all_companies(offset)
                result = json.loads(r.content)
                offset = result["offset"]

                for d in result["companies"]:
                    companyname = None
                    if "name" in d["properties"]:
                        companyname = d["properties"]["name"]["value"]
                    row = (d["companyId"], companyname)
                    spamwriter.writerow(row)
                if not result["has-more"]:
                    break

    @staticmethod
    def export_all_companies(filename):
        with open(filename, 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            spamwriter.writerow(("companyId", "companyname"))
            properties = ["name"]
            offset = ""
            while True:
                r = Company.get_page_companies(offset, properties)
                result = json.loads(r.content)
                offset = result["offset"]


                for d in result["companies"]:
                    try:
                        companyname = d["properties"]["name"]["value"]
                    except:
                        companyname = None
                    row = (d["companyId"],
                           companyname
                           )
                    spamwriter.writerow(row)
                if not result["has-more"]:
                    break