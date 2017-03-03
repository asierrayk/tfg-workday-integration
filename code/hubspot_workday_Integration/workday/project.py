import json, requests
from datetime import datetime
from lxml import etree as ET
from modules.xmlhelper import dict_to_xml

from modules.configuration import wd_cfg
from modules.configuration import mapping
from modules.database import db
from modules.log import logger


nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}


class Project:
    def __init__(self, project_dic): # name, id=None, custom_organization=None, start_date=None, currency=None, status=None,
                 # company=None, customer=None, dealid=None, position_id=None, hierarchy=None, optional_hierarchy=None):
        """
        self.name = name
        self.id = id
        self.custom_org = custom_organization
        self.start_date = start_date
        self.currency = currency
        self.status = status
        self.company = company
        self.customer = customer
        self.dealId = dealid
        self.position_id = position_id
        self.hierarchy = hierarchy
        self.optional_hierarchy = optional_hierarchy
        """
        attributes = ["name", "id", "custom_org", "start_date", "currency", "status", "company", "customer",
                      "dealId", "position_id", "hierarchy", "optional_hierarchy"]
        for a in attributes:
            self.__dict__[a] = project_dic.get(a)



    @classmethod
    def from_deal(cls, deal):
        project_dic={}
        project_dic["id"] = db.get_project(deal.dealId)
        project_dic["name"] = deal.dealname
        project_dic["dealId"] = deal.dealId
        project_dic["start_date"] = deal.closedate
        project_dic["currency"] = deal.transaction_currency
        project_dic["status"] = mapping.get("projectstatus", deal.dealstage)
        project_dic["company"] = mapping.get("company", deal.legal_entity)
        project_dic["position_id"] = mapping.get("position_id", deal.hubspot_owner_id)
        project_dic["customer"] = db.get_customer(str(deal.company_id)) if deal.company_id else None
        project_dic["hierarchy"] = "All_Projects"
        project_dic["optional_hierarchy"] = None #"Practice_PSOFT_Projects"

        if deal.practice in ["SAP", "ITC&S"]:
            d = json.loads(mapping.get("custom_org", deal.practice))
            if deal.transaction_currency != "ARS":
                project_dic["custom_organization"] = d["international"]
            else:
                project_dic["custom_organization"] = d["general"]
        else:
            project_dic["custom_organization"] = mapping.get("custom_org", deal.practice)


        return cls(project_dic)


    @classmethod
    def from_workday(cls, project_ID):
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": project_ID,
        }

        root = dict_to_xml(d, "root")

        xslt_root = ET.parse('xslt/Get_Projects.xslt')

        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        # Get the project
        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "project from wd " + str(r.status_code)
        print r.content

        project_dic = {}
        project_dic["id"] = project_ID
        project_dic["dealId"] = db.get_deal(project_ID)
        # Get the fields
        reply_soap = ET.fromstring(r.content)
        project_dic["name"] = reply_soap.find('.//wd:Project_Data/wd:Project_Name', namespaces=nsd).text
        project_dic["hierarchy"] = reply_soap.find('.//wd:Project_Data/wd:Project_Hierarchy_Reference/wd:ID[@wd:type="Project_Hierarchy_ID"]', namespaces=nsd).text
        dt = reply_soap.find('.//wd:Project_Data/wd:Start_Date', namespaces=nsd).text
        project_dic["start_date"] = datetime.strptime(dt, '%Y-%m-%d-%H:%M').date().strftime('%Y-%m-%d')
        project_dic["status"] = reply_soap.find('.//wd:Project_Data/wd:Project_Status_Reference/wd:ID[@wd:type="Project_Status_ID"]', namespaces=nsd).text
        project_dic["currency"] = reply_soap.find('.//wd:Project_Data/wd:Currency_Reference/wd:ID[@wd:type="Currency_ID"]', namespaces=nsd).text
        project_dic["company"] = reply_soap.find('.//wd:Project_Data/wd:Company_Reference/wd:ID[@wd:type="Company_Reference_ID"]', namespaces=nsd).text
        customer = reply_soap.find('.//wd:Project_Data/wd:Customer_Reference/wd:ID[@wd:type="Customer_ID"]', namespaces=nsd)
        project_dic["customer"] = customer.text if customer else None



        return cls(project_dic) #name=name, id=project_ID, start_date=start_date, status=status, dealid=db.get_deal(project_ID))


    def valid_to_submit(self): #TODO only requiered fields of project, notify by email
        return self.name and self.start_date and self.hierarchy

    def submit(self):
        '''Create a new project in workday'''
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project": self.__dict__
        }
        root = dict_to_xml(d, "root")

        print ET.tostring(root, method="html")

        xslt_root = ET.parse('xslt/Submit_Project.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")


        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "Submit Project " + str(r.status_code)
        print r.content

        if r.status_code != 200:
            logger.error("Submit_Project failed %s\n %s" % (r.status_code, r.content))
            return False

        logger.info("Submit_Project success")
        logger.debug("RESPONSE Submit_Project success" + r.content)

        # Get the WID and project_ID of the project created
        reply_soap = ET.fromstring(r.content)
        wid, self.id = map(lambda x: x.text, reply_soap.findall('.//wd:ID', namespaces=nsd))
        #print "wid " + wid
        print "project_ID " + self.id

        # Add to the db file the mapping between dealid (hubspot) and project_ID (Workday)
        db.insert("deal_project", self.dealId, self.id)
        return True

    def update(self):
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project": self.__dict__
        }
        root = dict_to_xml(d, "root")
        xslt_root = ET.parse('xslt/Update_Submit_Project.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        '''
        with open('tmp/soap_Update_Submit_Project_tmp.xml', 'w') as f:
            f.write(string_result)
        '''

        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "Update Project" + str(r.status_code)
        print r.content

        if r.status_code != 200:
            logger.error("Update_Submit_Project failed %s\n %s" % (r.status_code, r.content))
            return

    def assign_role(self, role):

        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": self.id,
            "position_id": self.position_id,
            "role": role
        }

        root = dict_to_xml(d, "root")
        xslt_root = ET.parse('xslt/Assign_Roles.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_staffing"), data=string_result)
        print "assign role " + str(r.status_code)
        print r.content

        if r.status_code != 200:
            logger.error("Assign_Roles failed %s\n %s" % (r.status_code, r.content))
            return

    def update_role(self, role):
        self.delete_roles(role)
        self.assign_role(role)

    def delete_roles(self, role): # "ASSIGNABLE_ROLE-6-231"

        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": self.id,
            "position_id": self.position_id,
            "role": role
        }

        root = dict_to_xml(d, "root")
        xslt_root = ET.parse('xslt/Delete_Roles.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_staffing"), data=string_result)
        print r.status_code
        print r.content

        if r.status_code != 200:
            logger.error("Delete_Roles failed. project_ID %s, role %s, position_ID" % (self.id, role, self.position_id))
            return False

        logger.info("Delete_Roles succeed %s\n %s" % (r.status_code, r.content))