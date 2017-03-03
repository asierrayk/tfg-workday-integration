from datetime import date

from modules.log import logger
import modules.mail as mail

from deal import Deal
from company import Company
from modules.configuration import mapping
from modules.database import db
from customer import Customer
from project import Project


def init():
    deals = Deal.get_all_deals()
    hits = 0
    fails = 0
    deals_fail = []
    for d in deals:
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
        deal_dic["company_id"] = p.get("company_id", {}).get("value")
        closedate_ms = d["properties"].get("closedate", {}).get("timestamp")
        deal_dic["closedate"] = date.fromtimestamp(closedate_ms / 1000.0).strftime('%Y-%m-%d') if closedate_ms else None
        deal = Deal(deal_dic)
        if not db.get_project(deal.dealId) or db.is_excluded(deal.dealId):
            rc = project_submit(deal)
            if rc:
                hits += 1
            else:
                fails += 1
                deals_fail.append(deal.dealID)

    print "%s pending projects submitted successfully" % hits
    print "%s pending projects failed at submit" % fails
    print deals_fail



def deal_creation(dealid, propertyChanged="dealname"):
    # If the project with same ID has been created, it doesn't create again.
    project_id = db.get_project(dealid)
    if project_id:
        logger.info("A project already has been created associated with the same deal. dealid %s, project_id %s", dealid, project_id)
        print "A project already has been created associated with the same deal. dealid %s, project_id %s" % (dealid, project_id)
        return False

    #deal = Deal.from_hubspot(38017627)  # TODO
    deal = Deal.from_hubspot(dealid, propertyChanged)
    project_submit(deal)


def project_submit(deal):
    if deal.dealstage not in dict(mapping.items("projectstatus")):
        logger.warning("Project not submitted, dealstage %s not valid for the deal %s is not valid" % (deal.dealstage, deal.dealId))
        print "Project not submitted, dealstage %s not valid for the deal %s is not valid" % (deal.dealstage, deal.dealId)
        return False

    project = Project.from_deal(deal)
    if project.valid_to_submit():
        # Submit the company associated
        if deal.company_id and not db.get_customer(deal.company_id):
            company = Company.from_hubspot(deal.company_id)
            customer = Customer.from_company(company)
            customer.submit()
        if project.submit():
            if project.position_id:
                project.assign_role("ASSIGNABLE_ROLE-6-231")
            return True
        else:
            logger.warning("Project error submitting. dealid %s" % deal.dealId)
            print "Project error submitting. dealid %s" % deal.dealId
            return False
    else:
        if deal.user_mail:
            try:
                mail.send(mail.defaults().get("notify-to"), "Deal %s not synchronized" % deal.dealId, "The deal %s can't be synchronized. Remember that dealname, closdate, 'hierarchy' must be filled")
                print "Mail sent to %s" % deal.user_mail
            except:
                print "Mail no pudo ser enviado a %s" % deal.user_mail
        logger.warning("Project not valid for submit. dealid %s" % deal.dealId)
        print "Project not valid for submit. dealid %s" % deal.dealId
        return False


def deal_change(dealid, propertyChanged):
    if propertyChanged == "dealstage":
        deal_stage_change(dealid, propertyChanged)
        # deal_stage_change(23738706)
    elif propertyChanged == "hubspot_owner_id":
        deal_owner_change(dealid, propertyChanged)
        # deal_owner_change(23738706)
    elif propertyChanged == "practice":
        deal_practice_change(dealid, propertyChanged)
    elif propertyChanged == "closedate":
        deal_close_date_change(dealid, propertyChanged)
    else:
        logger.warning("propertyChanged '%s' ignored" % propertyChanged)



def deal_stage_change(dealid, propertyChanged):
    # First of all, we need to get the project from workday since the web service we are using to update changes more than one field (not only the status). So wee need to get these fields
    project_ID = db.get_project(dealid)  # mapping.dealid[self.dealId]

    if not project_ID:
        return deal_creation(dealid)

    #deal = Deal.from_hubspot(23738706)  # TODO
    deal = Deal.from_hubspot(dealid, propertyChanged)

    if deal.dealstage not in mapping._sections["projectstatus"]:
        logger.warning("Project not changed, dealstage %s received is not valid" % deal.dealstage)
        return

    project = Project.from_workday(project_ID)

    project.status = mapping.get("projectstatus", deal.dealstage)
    project.update()


def deal_owner_change(dealid, propertyChanged):
    # First of all, we need to get the project from workday since the web service we are using to update changes more than one field (not only the status). So wee need to get these fields
    project_ID = db.get_project(dealid)  # mapping.dealid[self.dealId]

    if not project_ID:
        return deal_creation(dealid)

    # deal = Deal.from_hubspot(23738706)  # TODO
    deal = Deal.from_hubspot(dealid, propertyChanged)

    project = Project.from_workday(project_ID)

    project.position_id = mapping.get("position_id", deal.hubspot_owner_id)

    if project.position_id:
        project.update_role("ASSIGNABLE_ROLE-6-231")

def deal_practice_change(dealid, propertyChanged):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChanged)

def deal_close_date_change(dealid, propertyChanged):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChanged)