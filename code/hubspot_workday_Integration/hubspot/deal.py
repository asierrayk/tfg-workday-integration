import json
import datetime as dt

import requests
import unicodecsv as csv

from hubspot.authorization import hs_autho
from modules.configuration import mapping
from modules.log import logger

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Deal:
    attributes = ["dealId", "dealname", "practice", "closedate", "hubspot_owner_id", "dealstage", "legal_entity",
                  "transaction_currency", "opp_number", "company_id", "description"]
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

        self.__dict__["user_mail"] = deal_dic.get("user_mail")


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


        logger.info("RESPONSE HUBSPOT GET_DEAL 200\n\n")
        print "deal from hubspot " + str(r.status_code)

        result = json.loads(r.content)

        deal_dic = {}
        deal_dic["dealId"] = str(result["dealId"])

        properties = result["properties"]
        deal_dic["dealname"] = properties.get("dealname",{}).get("value")
        deal_dic["description"] = properties.get("description", {}).get("value")

        mail = properties.get(propertyChanged, {}).get("sourceId")
        deal_dic["user_mail"] = mail

        deal_dic["practice"] = properties.get("practice", {}).get("value")

        closedate_ms = properties.get("closedate", {}).get("value")
        ts = int(closedate_ms)/1000.0
        utc_hs_offset = dt.timedelta(0, 3600) #Difference between utc and the report settings of hubspot
        d = dt.datetime.utcfromtimestamp(ts) + utc_hs_offset
        deal_dic["closedate"] = d.strftime('%Y-%m-%d')



        deal_dic["hubspot_owner_id"] = properties.get("hubspot_owner_id",{}).get("value")
        deal_dic["dealstage"] = properties.get("dealstage", {}).get("value")
        deal_dic["legal_entity"] = properties.get("legal_entity", {}).get("value")
        deal_dic["transaction_currency"] = properties.get("transaction_currency", {}).get("value")

        deal_dic["opp_number"] = properties.get("opp_number", {}).get("value")
        companies = result.get("associations", {}).get("associatedCompanyIds", [])
        deal_dic["company_id"] = companies[0] if companies else None

        return cls(deal_dic)

    @staticmethod
    def get_page_deals(offset, properties, includeAssociations = True, propertiesWithHistory= False, limit="250"):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        #properties_params = reduce(lambda x, y: x+y, ["&properties=%s" % x for x in properties])
        params = []
        if includeAssociations:
            params += ["includeAssociations=true"]
        params += ["limit=%s" % limit]
        if propertiesWithHistory:
            params += ["propertiesWithHistory=%s" % x for x in properties]
        else:
            params += ["properties=%s" % x for x in properties]
        if offset:
            params += ["offset=%s" % offset]
        url = "https://api.hubapi.com/deals/v1/deal/paged?" + "&".join(params)
        r = requests.get(url, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_DEALS %s\n %s\n\n" % (r.status_code, r.content))
        return r

    @staticmethod
    def get_recent_deals(offset, includePropertyVersions= False, since=None, count="500"):
        if hs_autho.is_token_expired():
            hs_autho.refresh()

        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        properties = Deal.attributes
        params = []
        if since:
            params += ["since=%s" % since]
        params += ["count=%s" % count]
        if includePropertyVersions:
            params += ["includePropertyVersions=%s" % x for x in properties]
        else:
            params += ["properties=%s" % x for x in properties]
        if offset:
            params += ["offset=%s" % offset]

        url = "https://api.hubapi.com/deals/v1/deal/recent/created?" + "&".join(params)
        r = requests.get(url, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get(url, headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_DEALS %s\n %s\n\n" % (r.status_code, r.content))
        return r

    @classmethod
    def get_all_deals(cls, properties=None, includeAssociations=True, propertiesWithHistory=False):
        if not properties:
            properties = cls.attributes

        deals = []
        offset = ""
        while True:
            r = Deal.get_page_deals(offset, properties, includeAssociations, propertiesWithHistory)
            result = json.loads(r.content)
            offset = result["offset"]

            for d in result["deals"]:
                deals.append(d)
            if not result["hasMore"]:
                break

        return deals

    @classmethod
    def get_all_recent_deals(cls, includePropertyVersions=False):

        deals = []
        offset = ""
        while True:
            r = Deal.get_recent_deals(offset, includePropertyVersions)
            result = json.loads(r.content)
            offset = result["offset"]

            for d in result["results"]:
                deals.append(d)
            if not result["hasMore"]:
                break

        return deals

    @staticmethod
    def export_all_deals(filename):
        owners = {}
        with open(filename, 'w') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            spamwriter.writerow(("dealid", "dealname", "company", "practice", "legal_entity", "dealstage", "project_status", "opp_number", "owner_name", "owner_email"))
            properties = ["dealname", "hubspot_owner_id", "company", "practice", "legal_entity", "dealstage", "opp_number", "hubspot_owner_id"]
            offset = ""
            while True:
                r = Deal.get_page_deals(offset, properties)
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
                    else:
                        project_status = None
                    try:
                        opp_number = d["properties"]["opp_number"]["value"]
                    except:
                        opp_number = None
                    try:
                        hubspot_owner_id = d["properties"]["hubspot_owner_id"]["value"]
                    except:
                        hubspot_owner_id = None

                    if hubspot_owner_id in owners:
                        ho = owners.get(hubspot_owner_id)
                    else:
                        ho = Deal.get_hubspot_owner(hubspot_owner_id)
                        owners[hubspot_owner_id] = ho

                    owner_name = ho["firstName"] + ' ' + ho["lastName"]
                    owner_email = ho["email"]
                    row = (d["dealId"],
                           d["properties"]["dealname"]["value"],
                           company,
                           practice,
                           legal_entity,
                           dealstage,
                           project_status,
                           opp_number,
                           owner_name,
                           owner_email
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
        result = json.loads(r.content)
        return result

    @staticmethod
    def get_hubspot_owner(owner_id):
        headers = {"Authorization": "Bearer " + hs_autho.access_token}

        r = requests.get("http://api.hubapi.com/owners/v2/owners/" + owner_id, headers=headers)

        while r.status_code == 401:  # Code when the token has expired or is not valid
            if hs_autho.check_token_expired():
                hs_autho.refresh()
                headers = {"Authorization": "Bearer " + hs_autho.access_token}
                r = requests.get("http://api.hubapi.com/owners/v2/owners", headers=headers)

        if r.status_code != 200:
            logger.warning("RESPONSE HUBSPOT GET_ALL_OWNERS %s\n %s\n\n" % (r.status_code, r.content))
        result = json.loads(r.content)
        return result

if __name__=="__main__":
    Deal.export_all_deals()