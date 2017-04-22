from datetime import date

from workday.customer import Customer
from hubspot.deal import Deal

import modules.mail as mail
from hubspot.company import Company
from modules.configuration import mapping, mail_cfg
from modules.database import db
from modules.log import logger
from workday.project import Project
from helper import *



def deal_creation(dealid):
    """
    Handler of the event deal creation from HubSpot. Call project_submit in case that the deal is not aready in the DB.
    :param dealid: HubSpot id of the deal that has been created
    :return:
    """
    # If the project with same ID has been created, it doesn't create again.
    project_id = db.get_project(dealid)
    if project_id:
        logger.info("A project already has been created associated with the same deal. dealid %s, project_id %s", dealid, project_id)
        print "A project already has been created associated with the same deal. dealid %s, project_id %s" % (dealid, project_id)
        return False

    deal = Deal.from_hubspot(dealid)
    project_submit(deal)


def project_submit(deal):
    """
    In case that the deal is in a right stage, create a project using the deal and a customer.
    Then submit the customer and the project if they aren't already created.
    :param deal: deal Object
    :return: Boolean indicating if the project has been submitted successfully.
    """
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
            deal.update_opp_number(project.id)
            if project.position_id:
                pass
                #project.assign_role("ASSIGNABLE_ROLE-6-231")
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
    """
    Handler of the event deal change from HubSpot. Call to the corresponding method according to the propertyChanged
    :param dealid: HubSpot id of the deal changed
    :param propertyChanged: name of the property changed in HubSpot
    :return:
    """
    if db.is_excluded(dealid):
        logger.warning("Project not changed, the project is in a final status")
        return

    project_ID = db.get_project(dealid)
    if not project_ID:
        return deal_creation(dealid)

    deal = Deal.from_hubspot(dealid)

    if propertyChanged == "dealstage":
        deal_stage_change(deal, project_ID)
    elif propertyChanged == "hubspot_owner_id":
        deal_owner_change(deal, project_ID)
    elif propertyChanged == "practice":
        deal_practice_change(deal, project_ID)
    elif propertyChanged == "closedate":
        deal_closedate_change(deal, project_ID)
    elif propertyChanged == "description":
        deal_description_change(deal, project_ID)
    elif propertyChanged == "legal_entity":
        deal_legal_entity_change(deal, project_ID)
    elif propertyChanged == "dealname":
        deal_name_change(deal, project_ID)
    elif propertyChanged == "transaction_currency":
        deal_transaction_currency_change(deal, project_ID)
    elif propertyChanged == "associatedcompanyid":
        deal_associatedcompanyid_change(deal, project_ID)
    elif propertyChanged == "hs_lastmodifieddate":
        deal_hs_lastmodifieddate(deal, project_ID)
    else:
        logger.warning("propertyChanged '%s' ignored" % propertyChanged)


    if deal.opp_number != project_ID:
        deal.update_opp_number(project_ID)



def deal_stage_change(deal, project_ID):
    """
    Modify the project status according to the deal stage.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """

    if deal.dealstage not in mapping._sections["projectstatus"]:
        logger.warning("Project not changed, dealstage %s received is not valid" % deal.dealstage)
        return

    project = Project.from_workday(project_ID)

    new_status = mapping.get("projectstatus", deal.dealstage)
    if new_status != project.status:
        project.status = new_status
        project.update()
    else:
        logger.info("Project status same as the previous one. Not changed")


def deal_owner_change(deal, project_ID):
    """
    Modify the project optional hierarchy according to the deal hubspot_owner_id.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
    project = Project.from_workday(project_ID)

    emplid_positionid = mapping.get("emplid_positionid", deal.hubspot_owner_id).split(',')
    if not emplid_positionid:
        logger.info("Hubspot owner id %s is not mapped" % deal.hubspot_owner_id)
        return
    new_emplid, new_positionid = emplid_positionid

    '''
    if new_positionid == project.position_id:
        logger.warning("Project not changed, position_id %s received is the same as the previous one" % new_positionid)
        return
    if new_emplid == project.emplid:
        logger.warning("Project not changed, emplid %s received is the same as the previous one" % new_emplid)
        return
    '''

    project.emplid, project.position_id = emplid_positionid
    #project.update_role("ASSIGNABLE_ROLE-6-231")
    project.update_optional_hierarchy("CM_")



def deal_practice_change(deal, project_ID):
    """
    Modify the project custom organization according to the deal practice.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
    project = Project.from_workday(project_ID)

    new_custom_org = Project.get_custom_org(deal.practice, deal.transaction_currency)
    if project.custom_org == new_custom_org:
        logger.warning("Project practice not changed, practice: %s received is the same as the previous one" % new_custom_org)
        return
    project.custom_org = new_custom_org
    project.currency = deal.transaction_currency

    project.update()
    project.update_hierarchy(project.custom_org)


def deal_closedate_change(deal, project_ID):
    """
    Modify the project start_date according to the deal closedate.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
    project = Project.from_workday(project_ID)

    if project.start_date == deal.closedate:
        logger.warning("Project start date not changed, start_date: %s received is the same as the previous one" % deal.closedate)
        return
    project.start_date = deal.closedate

    project.update()


def deal_description_change(deal, project_ID):
    """
    Modify the project description according to the deal description.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """

    project = Project.from_workday(project_ID)

    if project.description == deal.description:
        logger.warning("Project description not changed, description: %s received is the same as the previous one" % deal.description)
        return
    project.description = deal.description

    project.update()

def deal_name_change(deal, project_ID):
    """
    Modify the project name according to the deal dame.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
    project = Project.from_workday(project_ID)


    if project.name == deal.dealname:
        logger.warning("Project name not changed, name: %s received is the same as the previous one" % deal.dealname)
        return
    project.name = deal.dealname
    project.update()


def deal_legal_entity_change(deal, project_ID):
    """
    Modify the project company according to the deal legal_entity.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
    project = Project.from_workday(project_ID)

    new_company = mapping.get("company", deal.legal_entity)
    if project.company == new_company:
        logger.warning("Project company not changed, company: %s received is the same as the previous one" % new_company)
        return
    project.company = new_company
    project.update()


def deal_transaction_currency_change(deal, project_ID):
    """
    Modify the project currency according to the deal transaction_currency.
    :param deal: object representing the deal changed
    :param project_ID: id of the project linked to the deal
    :return:
    """
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

def deal_hs_lastmodifieddate(deal, project_ID):
    project = Project.from_workday(project_ID)
    new_customer = db.get_customer(deal.company_id)
    if project.customer == new_customer:
        logger.warning(
            "Project customer not changed, customer: %s received is the same as the previous one" % new_customer)
        return

    if deal.company_id and not new_customer:
        company = Company.from_hubspot(deal.company_id)
        customer = Customer.from_company(company)
        customer.submit()


    project.customer = new_customer
    project.update()
