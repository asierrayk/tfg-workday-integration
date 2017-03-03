import json
import requests

import unicodecsv as csv

from customer import Customer
from modules.authorization import hs_autho
from modules.database import db
from modules.log import logger

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Company:
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
            logger.warning("RESPONSE HUBSPOT GET_DEAL %s\n %s\n\n" % (r.status_code, r.content))
            print "RESPONSE HUBSPOT GET_DEAL %s\n %s\n\n" % (r.status_code, r.content)
            return

        print "company from hs " + str(r.status_code)
        print r.content
        result = json.loads(r.content)

        company_dic = {}
        company_dic["id"] = str(result["companyId"])

        company_dic.update({k: v.get("value") for k, v in result.get("properties", {}).items()})

        return cls(company_dic)



    @staticmethod
    def get_all_companies(offset=""):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}
        # TODO at csv must be included dealid, dealname, owner, practica, cliente, sociedad

        p = ["name"]
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
            logger.warning("RESPONSE HUBSPOT GET_ALL_DEALS %s\n %s\n\n" % (r.status_code, r.content))
        return r

    def export_all_companies(self):
        with open('output/all_companies.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            spamwriter.writerow(("companyid", "companyname"))
            offset = ""
            while True:
                r = self.get_all_companies(offset)
                result = json.loads(r.content)
                offset = result["offset"]
                print result

                for d in result["companies"]:
                    companyname = None
                    if "name" in d["properties"]:
                        companyname = d["properties"]["name"]["value"]
                    row = (d["companyId"], companyname)
                    spamwriter.writerow(row)
                if not result["has-more"]:
                    break


    def submit_customer(self):
        # If the project with same ID has been created, it doesn't create again.
        c = db.get_customer(self.id)
        if c:
            logger.info("Customer %s is already submitted", c)
            return

        customer = Customer.from_deal(self)
        customer.submit()