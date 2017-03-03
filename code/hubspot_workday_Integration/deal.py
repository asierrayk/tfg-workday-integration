import json
from datetime import date

import requests
import unicodecsv as csv

from company import Company
from customer import Customer
from modules.authorization import hs_autho
from modules.log import logger
from modules.configuration import mapping
from modules.database import db
from project import Project

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Deal:
    attributes = ["dealId", "dealname", "practice", "closedate", "hubspot_owner_id", "dealstage", "legal_entity",
                  "transaction_currency", "opp_number", "company_id", "user_mail"]
    def __init__(self, deal_dic):
        """
        self.name = name
        self.practice = practice
        self.closedate = closedate
        self.hubspot_owner_id  = hubspot_owner_id
        self.dealstage = dealstage
        self.legal_entity  = legal_entity
        self.transaction_currency = transaction_currency
        self.opp_number = opp_number
        self.company_id = company_id
        self.id = id
        """
        for a in self.attributes:
            self.__dict__[a] = deal_dic.get(a)


    @classmethod
    def from_hubspot(cls, objectId, propertyChanged="dealname"):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}
        r = requests.get("https://api.hubapi.com/deals/v1/deal/" + str(objectId), headers=headers)

        while r.status_code == 401: # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("https://api.hubapi.com/deals/v1/deal/" + str(objectId), headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_DEAL %s\n %s\n\n" % (r.status_code, r.content))
            return


        logger.info("RESPONSE HUBSPOT GET_DEAL 200\n\n" + r.content)
        print "deal from hubspot " + str(r.status_code)
        print r.content

        result = json.loads(r.content)

        deal_dic = {}
        deal_dic["dealId"] = str(result["dealId"])

        properties = result["properties"]
        deal_dic["dealname"] = properties.get("dealname",{}).get("value")
        mail = properties.get(propertyChanged, {}).get("sourceId")
        deal_dic["user_mail"] = mail

        deal_dic["practice"] = properties.get("practice", {}).get("value")

        closedate_ms = properties.get("closedate", {}).get("timestamp")
        deal_dic["closedate"] = date.fromtimestamp(closedate_ms/1000.0).strftime('%Y-%m-%d') if closedate_ms else None
        deal_dic["hubspot_owner_id"] = properties.get("hubspot_owner_id",{}).get("value")
        deal_dic["dealstage"] = properties.get("dealstage", {}).get("value")
        deal_dic["legal_entity"] = properties.get("legal_entity", {}).get("value")
        deal_dic["transaction_currency"] = properties.get("transaction_currency", {}).get("value")

        deal_dic["opp_number"] = properties.get("opp_number", {}).get("value")
        companies = result.get("associations", {}).get("associatedCompanyIds", [])
        deal_dic["company_id"] = companies[0] if companies else None

        return cls(deal_dic)

    @staticmethod
    def get_page_deals(offset, params):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}
        # TODO at csv must be included dealid, dealname, owner, practica, cliente, sociedad

        properties = reduce(lambda x, y: x+y, ["&properties=%s"%x for x in params])
        offset_parameter = ""
        if offset:
            offset_parameter = "&offset=%s" % offset
        parameters = properties + offset_parameter
        r = requests.get("https://api.hubapi.com/deals/v1/deal/paged?includeAssociations=true&limit=250" + parameters, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("https://api.hubapi.com/deals/v1/deal/paged?includeAssociations=true&limit=250" + parameters,headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_DEALS %s\n %s\n\n" % (r.status_code, r.content))
        return r

    @classmethod
    def get_all_deals(cls):
        deals = []
        offset = ""
        while True:
            r = Deal.get_page_deals(offset, cls.attributes)
            result = json.loads(r.content)
            offset = result["offset"]

            for d in result["deals"]:
                deals.append(d)
            if not result["hasMore"]:
                break

        return deals

    @staticmethod
    def export_all_deals():
        with open('output/all_deals.csv', 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            spamwriter.writerow(("dealid", "dealname", "company", "practice", "legal_entity", "dealstage", "project_status", "opp_number"))
            params = ["dealname", "hubspot_owner_id", "company", "practice", "legal_entity", "dealstage", "opp_number"]
            offset = ""
            while True:
                r = Deal.get_page_deals(offset, params)
                result = json.loads(r.content)
                offset = result["offset"]

                for d in result["deals"]:
                    try:
                        company = d["associations"]["associatedCompanyIds"][0]
                    except:
                        company = None
                    try:
                        practice = d["properties"]["practice"]["value"]
                    except:
                        practice = None
                    try:
                        legal_entity = d["properties"]["legal_entity"]["value"]
                    except:
                        legal_entity = None

                    dealstage = d["properties"]["dealstage"]["value"]
                    if mapping.has_option("projectstatus", dealstage):
                        project_status = mapping.get("projectstatus", dealstage)

                    try:
                        opp_number = d["properties"]["opp_number"]["value"]
                    except:
                        opp_number = None
                    else:
                        project_status = None
                    row = (d["dealId"],
                           d["properties"]["dealname"]["value"],
                           company,
                           practice,
                           legal_entity,
                           dealstage,
                           project_status,
                           opp_number
                           )
                    spamwriter.writerow(row)
                if not result["hasMore"]:
                    break


    @staticmethod
    def get_hubspot_owners():
        "Used to map the hubspot_owner_id with position_ID (Workday)"
        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        r = requests.get("http://api.hubapi.com/owners/v2/owners", headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("http://api.hubapi.com/owners/v2/owners", headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_OWNERS %s\n %s\n\n" % (r.status_code, r.content))
        print r.content
        result = json.loads(r.content)
        for o in result:
            mapping.update("position_id", str(o["ownerId"]), (o["firstName"] + " " + o["lastName"]).encode('utf8'))
        return r

