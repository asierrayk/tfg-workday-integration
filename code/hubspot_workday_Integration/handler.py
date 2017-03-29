from datetime import date

from workday.customer import Customer
from hubspot.deal import Deal

import modules.mail as mail
from hubspot.company import Company
from modules.configuration import mapping, mail_cfg
from modules.database import db
from modules.log import logger
from workday.project import Project



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
        closedate_ms = d["properties"].get("closedate", {}).get("timestamp")
        deal_dic["closedate"] = date.fromtimestamp(closedate_ms / 1000.0).strftime('%Y-%m-%d') if closedate_ms else None
        deal = Deal(deal_dic)
        if not db.get_project(deal.dealId) or db.is_excluded(deal.dealId):
            rc = project_submit(deal)
            if rc:
                hits += 1
            else:
                fails += 1
                deals_fail.append(deal.dealId)

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

    deal = Deal.from_hubspot(dealid, propertyChanged)
    project_submit(deal)


def project_submit(deal):
    if deal.dealstage not in dict(mapping.items("projectstatus")):
        logger.warning("Project not submitted, dealstage %s not valid for the deal %s is not valid" % (deal.dealstage, deal.dealId))
        print "Project not submitted, dealstage %s not valid for the deal %s is not valid" % (deal.dealstage, deal.dealId)
        return False

    if deal.dealstage == "closedlost":
        logger.warning("Project not submitted, dealstage is closedlost")
        print "Project not submitted, dealstage is closedlost"
        return False


    # Submit the company associated
    if deal.company_id and not db.get_customer(deal.company_id):
        company = Company.from_hubspot(deal.company_id)
        customer = Customer.from_company(company)
        customer.submit()

    project = Project.from_deal(deal)

    if project.valid_to_submit():
        if project.submit():
            if project.position_id:
                pass
                #project.assign_role("ASSIGNABLE_ROLE-6-231")
            return True
        else:
            logger.warning("Project error submitting. dealid %s" % deal.dealId)
            print "Project error submitting. dealid %s" % deal.dealId
            return False
    else:
        if deal.user_mail:
            logger.warning("Project not valid for submit. dealid %s" % deal.dealId)
            print "Project not valid for submit. dealid %s" % deal.dealId
            try:
                #TODO change destination address
                subject = mail_cfg.get("dealnotvalid", "subject").replace("_dealid_", deal.dealId)
                content = mail_cfg.get("dealnotvalid", "content").replace("_dealid_", deal.dealId).replace("_dealname_", deal.dealname)
                mail.send(mail_cfg.defaults().get("notify-to"), subject, content)

                logger.info("Mail sent to %s" % deal.user_mail)
                print "Mail sent to %s" % deal.user_mail
            except:
                logger.warning("Mail no pudo ser enviado a %s" % deal.user_mail)
                print "Mail no pudo ser enviado a %s" % deal.user_mail
        return False


def deal_change(dealid, propertyChanged):
    if db.is_excluded(dealid):
        logger.warning("Project not changed, the project is in a final status")
        return

    if propertyChanged == "dealstage":
        deal_stage_change(dealid, propertyChanged)
    elif propertyChanged == "hubspot_owner_id":
        deal_owner_change(dealid, propertyChanged)
    elif propertyChanged == "practice":
        deal_practice_change(dealid, propertyChanged)
    elif propertyChanged == "closedate":
        deal_closedate_change(dealid, propertyChanged)
    elif propertyChanged == "description":
        deal_description_change(dealid, propertyChanged)
    elif propertyChanged == "legal_entity":
        deal_legal_entity_change(dealid, propertyChanged)
    elif propertyChanged == "dealname":
        deal_name_change(dealid, propertyChanged)
    elif propertyChanged == "transaction_currency":
        deal_transaction_currency_change(dealid, propertyChanged)
    else:
        logger.warning("propertyChanged '%s' ignored" % propertyChanged)



def deal_stage_change(dealid, propertyChanged):
    # First of all, we need to get the project from workday since the web service we are using to update changes more than one field (not only the status). So wee need to get these fields
    project_ID = db.get_project(dealid)

    if not project_ID:
        return deal_creation(dealid)

    deal = Deal.from_hubspot(dealid, propertyChanged)

    if deal.dealstage not in mapping._sections["projectstatus"]:
        logger.warning("Project not changed, dealstage %s received is not valid" % deal.dealstage)
        return

    project = Project.from_workday(project_ID)

    new_status = mapping.get("projectstatus", deal.dealstage)
    if new_status != project.status:
        project.status = new_status
        project.update()
    else:
        logger.info("Project status ame as the previous one. Not changed")


def deal_owner_change(dealid, propertyChanged):
    # First of all, we need to get the project from workday since the web service we are using to update changes more than one field (not only the status). So wee need to get these fields
    project_ID = db.get_project(dealid)

    if not project_ID:
        return deal_creation(dealid)

    deal = Deal.from_hubspot(dealid, propertyChanged)

    project = Project.from_workday(project_ID)

    emplid_positionid = mapping.get("emplid_positionid", deal.hubspot_owner_id).split(',')
    if not emplid_positionid:
        logger.info("Hubspot owner id %s is not mapped" % deal.hubspot_owner_id)
        return
    new_emplid, new_positionid = emplid_positionid

    if new_positionid == project.position_id:
        logger.warning("Project not changed, position_id %s received is the same as the previous one" % new_positionid)
        return
    if new_emplid == project.emplid:
        logger.warning("Project not changed, emplid %s received is the same as the previous one" % new_emplid)
        return

    project.emplid, project.position_id = emplid_positionid
    #project.update_role("ASSIGNABLE_ROLE-6-231")
    project.update_optional_hierarchy("CM_")



def deal_practice_change(dealid, propertyChanged):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChanged)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)

    new_custom_org = Project.get_custom_org(deal.practice, deal.transaction_currency)
    if project.custom_org == new_custom_org:
        logger.warning("Project practice not changed, practice: %s received is the same as the previous one" % new_custom_org)
        return
    project.custom_org = new_custom_org
    project.currency = deal.transaction_currency

    project.update()
    project.update_hierarchy(project.custom_org)


def deal_closedate_change(dealid, propertyChanged):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChanged)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)

    #TODO debug
    logger.debug("DEAL\n %s" % deal.closedate)
    logger.debug("OLD closedate\n %s" % project.start_date)

    if project.start_date == deal.closedate:
        logger.warning("Project start date not changed, start_date: %s received is the same as the previous one" % deal.closedate)
        return
    project.start_date = deal.closedate

    project.update()


def deal_description_change(dealid, propertyChange):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChange)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)

    if project.description == deal.description:
        logger.warning("Project description not changed, description: %s received is the same as the previous one" % deal.description)
        return
    project.description = deal.description

    project.update()

def deal_name_change(dealid, propertyChange):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChange)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)


    if project.name == deal.dealname:
        logger.warning("Project name not changed, name: %s received is the same as the previous one" % deal.dealname)
        return
    project.name = deal.dealname
    project.update()


def deal_legal_entity_change(dealid, propertyChange):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChange)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)

    new_company = mapping.get("company", deal.legal_entity)
    if project.company == new_company:
        logger.warning("Project company not changed, company: %s received is the same as the previous one" % new_company)
        return
    project.company = new_company
    project.update()


def deal_transaction_currency_change(dealid, propertyChange):
    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid, propertyChange)

    deal = Deal.from_hubspot(dealid)
    project = Project.from_workday(project_ID)

    if project.currency == deal.transaction_currency:
        logger.warning("Project currency not changed, currency: %s received is the same as the previous one" % deal.transaction_currency)
        return
    project.currency = deal.transaction_currency
    new_custom_org = Project.get_custom_org(deal.practice, deal.transaction_currency)
    if project.custom_org != new_custom_org:
        project.custom_org = new_custom_org
        project.update_hierarchy(project.custom_org)
    project.update()
