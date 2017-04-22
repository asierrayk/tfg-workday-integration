from datetime import date
from hubspot.deal import Deal
from hubspot.company import Company
from workday.project import Project
from workday.customer import Customer

from modules.log import logger
from modules.configuration import mail_cfg
import modules.mail as mail
from modules.database import db

def init():
    """
    This process submit to workday all the deals of HubSpot
    :return:
    """
    deals = Deal.get_all_deals()
    hits = 0
    fails = 0
    deals_fail = []
    deals_in_progress = [d for d in deals and d.get("properties", {}).get("dealstage", {}).get("value")]
    for d in deals_in_progress:
        deal_dic = {}
        deal_dic["dealId"] = str(d["dealId"])
        companies = d.get("associations", {}).get("associatedCompanyIds")
        deal_dic["company_id"] = companies[0] if companies else None
        #deal_dic.update({k: v["value"] for k, v in d["properties"].items()})

        p = d.get("properties", {})

        deal_dic["dealname"] = p.get("dealname", {}).get("value")
        deal_dic["practice"] = p.get("practice", {}).get("value")
        deal_dic["hubspot_owner_id"] = p.get("hubspot_owner_id", {}).get("value")
        deal_dic["dealstage"] = p.get("dealstage", {}).get("value")
        deal_dic["legal_entity"] = p.get("legal_entity", {}).get("value")
        deal_dic["transaction_currency"] = p.get("transaction_currency", {}).get("value")
        deal_dic["opp_number"] = p.get("opp_number", {}).get("value")
        closedate_ms = d["properties"].get("closedate", {}).get("timestamp")
        deal_dic["closedate"] = date.fromtimestamp(closedate_ms / 1000.0).strftime('%Y-%m-%d') if closedate_ms else None
        deal = Deal(deal_dic)
        if not db.get_project(deal.dealId) and not db.is_excluded(deal.dealId):
            rc = project_submit(deal)
            if rc:
                hits += 1
            else:
                fails += 1
                deals_fail.append(deal.dealId)

    print "%s pending projects submitted successfully" % hits
    print "%s pending projects failed at submit" % fails
    print deals_fail


def check_deal_sync(dealid):
    """
    Check if the data in Workday differs from the data in HubSpot
    :param dealid: id of HubSpot deal
    :return: list containing the project attributes that aren't synchronized
    """
    differs = []
    deal = Deal.from_hubspot(dealid)

    new_project = Project.from_deal(deal)

    project_id = db.get_project(dealid)
    if not project_id:
        return None
    project = Project.from_workday(project_id)

    fields = ["id","dealId","name","hierarchy","start_date","status","currency","company","customer"]
    for f in fields:
        if project.__dict__[f] != new_project.__dict__[f]:
            differs.append(f)
    if new_project.__dict__["optional_hierarchy"] not in project.__dict__["optional_hierarchy"]:
        differs.append("optional_hierarchy")


    return differs


def find_unsync_deals():
    """
    Explore the deals created in the last month and check if they are synchronized with the Workday project.
    :return: list of deals that is not linked to a Workday project
    """

    deals = Deal.get_all_recent_deals()
    unsync = []

    for d in deals:
        dealid = d["dealId"]
        if check_deal_sync(dealid):
            unsync.append(dealid)

    return unsync

def find_missed_deals():
    """
    Explore the deals created in the las month and check if they are linked to a project.
    :return: list of deals that is not linked to a Workday project
    """

    deals = Deal.get_all_recent_deals()
    missed = []

    for d in deals:
        dealid = d["dealId"]
        project_id = db.get_project(dealid)
        if not project_id:
            missed.append(dealid)

    return missed


