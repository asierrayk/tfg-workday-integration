import json, requests
from datetime import datetime
from lxml import etree as ET
from dicttoxml import dicttoxml

from modules.configuration import wd_cfg
from modules.configuration import mapping
from modules.database import db
from modules.log import logger
from hierarchy import Hierarchy

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}




class Project:
    """
    Object representing a Project Workday object
    """
    attributes = ["name", "id", "custom_org", "start_date", "currency", "status", "company", "customer",
                  "dealId", "position_id", "hierarchy", "optional_hierarchy", "description"]

    def __init__(self, project_dic):
        for a in self.attributes:
            self.__dict__[a] = project_dic.get(a)



    @classmethod
    def from_deal(cls, deal):
        """
        Constructor from a given HubSpot deal
        :param deal: deal object
        :return:
        """
        project_dic={}
        project_dic["id"] = db.get_project(deal.dealId)
        project_dic["name"] = deal.dealname
        project_dic["description"] = deal.description

        project_dic["dealId"] = deal.dealId
        project_dic["start_date"] = deal.closedate
        project_dic["currency"] = deal.transaction_currency
        project_dic["status"] = mapping.get("projectstatus", deal.dealstage)
        project_dic["company"] = mapping.get("company", deal.legal_entity)
        emplid, positionid = mapping.get("emplid_positionid", deal.hubspot_owner_id).split(',')
        project_dic["emplid"] = emplid
        project_dic["position_id"] = positionid
        project_dic["customer"] = db.get_customer(str(deal.company_id)) if deal.company_id else None

        custom_org = Project.get_custom_org(deal.practice, deal.transaction_currency)
        project_dic["custom_org"] = custom_org

        project_dic["hierarchy"] = custom_org if custom_org else "All_Projects" #principal hierarchy id same as custom_org
        project_dic["optional_hierarchy"] = "CM_" + emplid
        project_dic["description"] = deal.description


        return cls(project_dic)


    @staticmethod
    def get_custom_org(practice, transaction_currency):
        """
        Depending on the practice and transaction_currency of the deal  compute the custom_org and retrieve it.
        :param practice: attribute practice of the deal object
        :param transaction_currency: attribute transaction of the deal object.
        :return: custom_org attribute of the project object
        """
        if practice in ["SAP", "ITC&S"]:
            d = json.loads(mapping.get("custom_org", practice))
            if transaction_currency != "ARS":
                return d["international"]
            else:
                return d["general"]
        else:
            return mapping.get("custom_org", practice)

    @classmethod
    def from_workday(cls, project_ID):
        """
        Constructor from a given a project id from Workday using web services
        :param project_ID: id of the Workday Project
        :return:
        """
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": project_ID,
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)

        xslt_root = ET.parse('xslt/Get_Projects.xslt')

        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        # Get the project
        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "project from wd " + str(r.status_code)


        if r.status_code != 200:
            logger.error("Project from wd failed %s\n %s" % (r.status_code, r.content))
            return
        logger.info("Project from wd success.")

        project_dic = {}
        project_dic["id"] = project_ID
        project_dic["dealId"] = db.get_deal(project_ID)
        # Get the fields
        reply_soap = ET.fromstring(r.content)
        project_dic["name"] = reply_soap.find('.//wd:Project_Data/wd:Project_Name', namespaces=nsd).text
        project_dic["hierarchy"] = reply_soap.find('.//wd:Project_Data/wd:Project_Hierarchy_Reference/wd:ID[@wd:type="Project_Hierarchy_ID"]', namespaces=nsd).text
        optionals = reply_soap.findall('.//wd:Project_Data/wd:Optional_Project_Hierarchy_Reference',namespaces=nsd)
        project_dic["optional_hierarchy"] = [o.find('wd:ID[@wd:type="Project_Hierarchy_ID"]',namespaces=nsd).text for o in optionals]
        dt = reply_soap.find('.//wd:Project_Data/wd:Start_Date', namespaces=nsd).text
        project_dic["start_date"] = datetime.strptime(dt, '%Y-%m-%d-%H:%M').date().strftime('%Y-%m-%d')
        project_dic["status"] = reply_soap.find('.//wd:Project_Data/wd:Project_Status_Reference/wd:ID[@wd:type="Project_Status_ID"]', namespaces=nsd).text
        project_dic["currency"] = reply_soap.find('.//wd:Project_Data/wd:Currency_Reference/wd:ID[@wd:type="Currency_ID"]', namespaces=nsd).text
        company = reply_soap.find('.//wd:Project_Data/wd:Company_Reference/wd:ID[@wd:type="Company_Reference_ID"]', namespaces=nsd)
        project_dic["company"] = company.text if company is not None else None
        customer = reply_soap.find('.//wd:Project_Data/wd:Customer_Reference/wd:ID[@wd:type="Customer_ID"]', namespaces=nsd)

        project_dic["customer"] = customer.text if customer is not None else None

        return cls(project_dic)


    def valid_to_submit(self):
        """
        compute if the project if valid for submit
        :return: Boolean indicating if the project is valid
        """
        return self.name and self.start_date and self.hierarchy

    def submit(self):
        '''
        Create a new project in workday
        :return: Boolean indicating if the operation has been completed successfully
        '''

        params = {key: value for key, value in self.__dict__.items() if value}
        params["external_project_reference"] = self.dealId
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project": params
        }
        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)

        xslt_root = ET.parse('xslt/Submit_Project.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "Submit Project " + str(r.status_code)

        if r.status_code != 200:
            logger.error("Submit_Project failed %s\n %s" % (r.status_code, r.content))
            return False



        # Get the WID and project_ID of the project created
        reply_soap = ET.fromstring(r.content)
        wid, self.id = map(lambda x: x.text, reply_soap.findall('.//wd:ID', namespaces=nsd))


        # Add to the db file the mapping between dealid (hubspot) and project_ID (Workday)
        db.insert("deal_project", self.dealId, self.id)
        #self.put_mapping()

        logger.info("Submit_Project success. dealid %s, Project_ID %s" % (self.dealId, self.id))
        print "project_ID " + self.id

        if self.status == mapping.get("projectstatus", "closedwon"):
            db.insert_excluded(self.dealId)

        return True

    def update(self):
        """
        Update an the corresponding existing project in Workday
        :return: Boolean indicating if the operation has been completed successfully
        """
        params = {key: value for key, value in self.__dict__.items() if value}
        params["external_project_reference"] = self.dealId
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project": params
        }
        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)
        xslt_root = ET.parse('xslt/Update_Submit_Project.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        logger.debug(string_result)


        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        logger.debug("Update Project" + str(r.status_code))
        logger.debug(r.content)

        if r.status_code != 200:
            logger.error("Update_Submit_Project failed %s\n %s" % (r.status_code, r.content))
            return
        logger.info("Update_Submit_Project success. project_ID %s" % self.id)

        if self.status in [mapping.get("projectstatus", s) for s in ["closedlost", "closedwon"]]:
            db.insert_excluded(self.dealId)

    def update_hierarchy(self, new_hierarchy_id):
        """
        Add a project to a given main hierarchy and remove it from the previous one. After that it submit the changes in both hierarchies
        :param new_hierarchy_id: id of the new project hierarchy
        :return:
        """
        # Workday reference id of practice hierarchy is the same as the practice id

        if new_hierarchy_id == self.hierarchy:
            logger.info("Hierarchy not updated. The project %s already has %s as practice hierarchy" % (self.id, new_hierarchy_id))
            return

        old_hierarchy = Hierarchy.from_workday(self.hierarchy)
        old_hierarchy.remove_included_project(self.id)

        self.hierarchy = new_hierarchy_id

        new_hierarchy = Hierarchy.from_workday(self.hierarchy)
        new_hierarchy.add_included_project(self.id)


    def update_optional_hierarchy(self, prefix):
        """
        Add a project to a given optional hierarchy and remove it from the previous one. After that it submit the changes in both hierarchies
        :param new_hierarchy_id: id of the new project hierarchy
        :return:
        """
        old_hierarchy = next(iter([x for x in self.optional_hierarchy if x.startswith(prefix)]), None)


        new_hierarchy = prefix + self.emplid
        if old_hierarchy == new_hierarchy:
            logger.info("Optional hierarchy not updated. The project %s already has %s as customer manager optional hierarchy" % (self.id, new_hierarchy))
            return

        if old_hierarchy:
            old_cm_hierarchy = Hierarchy.from_workday(old_hierarchy)
            old_cm_hierarchy.remove_included_project(self.id)

        new_cm_hierarchy = Hierarchy.from_workday(new_hierarchy)
        new_cm_hierarchy.add_included_project(self.id)



    def assign_role(self, role):
        """
        Assign a given role to the employee corresponding to the position_id attribute of the project
        :param role: Organization_Role_ID to be assigned
        :return:
        """
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": self.id,
            "position_id": self.position_id,
            "role": role
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)
        xslt_root = ET.parse('xslt/Assign_Roles.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")
        r = requests.post(wd_cfg.get("wws", "url_staffing"), data=string_result)
        print "assign role " + str(r.status_code)

        if r.status_code != 200:
            logger.error("Assign_Roles failed %s\n %s" % (r.status_code, r.content))
            return
        logger.info("Assign_Roles success. project_ID  %s, Customer Manager %s" % (self.id, self.position_id))

    def update_role(self, role):
        """
        Delete the previous roles and add a new one.
        :param role: Organization_Role_ID of the role to be updated
        :return:
        """
        self.delete_roles(role)
        self.assign_role(role)

    def delete_roles(self, role):
        """
        Delete the assigned employee to certain role
        :param role: Organization_Role_ID to be cleared
        :return:
        """
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "project_id": self.id,
            "position_id": self.position_id,
            "role": role
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)
        xslt_root = ET.parse('xslt/Delete_Roles.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_staffing"), data=string_result)
        print "delete role " + str(r.status_code)

        if r.status_code != 200:
            logger.error("Delete_Roles failed. project_ID %s, role %s, position_ID %s \n%s" % (self.id, role, self.position_id, r.content))
            return False
        logger.info("Delete_Roles succeed %s" % r.status_code)


    def put_mapping(self):
        """
        Add the deal_id project_id relation to the Integration_Worktag_Mapping
        :return:
        """
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "mapping_name": "HubSpot Deals"
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)
        xslt_root = ET.parse('xslt/get_Integration_Worktag_Mapping.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_financial_management"), data=string_result)
        print "get mappings " + str(r.status_code)

        if r.status_code != 200:
            logger.error("Get_Integration_Worktag_Mapping failed. %s \n%s" % (r.status_code, r.content))
            return False
        logger.info("Get_Integration_Worktag_Mapping succeed")

        reply_soap = ET.fromstring(r.content)

        mapping_detail = reply_soap.findall('.//wd:Response_Data/wd:Integration_Worktag_Mapping_Data',namespaces=nsd)
        external_code = [m.find('wd:Mapping_Detail/wd:External_Code') for m in mapping_detail]

        integration_mappings = []
        for m in mapping_detail:
            external_code = m.find('wd:Mapping_Detail/wd:External_Code')
            project_id = m.find('wd:Mapping_Detail/wd:ID[@wd:type="Project_ID"]')
            integration_mappings.append({"external_code": external_code, "project_id": project_id})

        integration_mappings.append({"external_code": self.dealId, "project_id": self.id})

        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "mapping_name": "HubSpot Deals",
            "source": "HubSpot_CRM",
            "integration_mappings": integration_mappings
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)
        xslt_root = ET.parse('xslt/Put_Integration_Worktag_Mapping.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_financial_management"), data=string_result)
        print "put mappings " + str(r.status_code)

        if r.status_code != 200:
            logger.error("Put_Integration_Worktag_Mapping failed. %s \n%s" % (r.status_code, r.content))
            return False
        logger.info("Put_Integration_Worktag_Mapping succeed")
