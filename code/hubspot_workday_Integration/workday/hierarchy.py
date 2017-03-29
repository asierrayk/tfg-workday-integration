from modules.configuration import wd_cfg
# from modules.xmlhelper import dict_to_xml
from dicttoxml import dicttoxml
from modules.log import logger
from lxml import etree as ET
import requests

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}


class Hierarchy:
    attributes = ["id", "name", "enable_as_optional", "status", "currency", "included_projects"]

    def __init__(self, hierarchy_dic):
        for h in self.attributes:
            self.__dict__[h] = hierarchy_dic[h]

    @classmethod
    def from_workday(cls, optional_hierarchy):
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "optional_hierarchy": optional_hierarchy,
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)

        xslt_root = ET.parse('xslt/Get_Workday_Project_Hierarchies.xslt')

        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        # Get the hierarchy
        r = requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)
        print "hierarchy from wd " + str(r.status_code)

        if r.status_code != 200:
            logger.error("hierarchy from wd failed %s\n %s" % (r.status_code, r.content))
            return
        logger.info("hierarchy from wd success.")


        rp = ET.fromstring(r.content)

        h_dic = {}
        h_dic["id"] = rp.find('.//wd:Project_Hierarchy_Data/wd:Project_Hierarchy_ID', namespaces=nsd).text
        h_dic["name"] = rp.find('.//wd:Project_Hierarchy_Data/wd:Project_Hierarchy_Name', namespaces=nsd).text
        enable_as_optional = rp.find('.//wd:Project_Hierarchy_Data/wd:Enable_as_Optional_Hierarchy', namespaces=nsd).text
        h_dic["enable_as_optional"] = enable_as_optional == '1'
        h_dic["status"] = rp.find('.//wd:Project_Hierarchy_Data/wd:Project_Hierarchy_Status_Reference/wd:ID[@wd:type="Document_Status_ID"]', namespaces=nsd).text
        currency = rp.find('.//wd:Project_Hierarchy_Data/wd:Reporting_Currency_Reference/wd:ID[@wd:type="Currency_ID"]', namespaces=nsd)
        h_dic["currency"] = currency.text if currency else None
        projects = rp.findall('.//wd:Project_Hierarchy_Data/wd:Included_Projects_in_Optional_Hierarchy_Reference', namespaces=nsd)
        h_dic["included_projects"] = {p.find('wd:ID[@wd:type="Project_ID"]', namespaces=nsd).text for p in projects}

        return cls(h_dic)

    def add_included_project(self, project_id):
        if self.enable_as_optional:
            self.included_projects.add(project_id)
            r = self.submit_included_projects()
        else:
            self.included_projects = [project_id]
            r = self.submit_included_projects()

        if r.status_code != 200:
            logger.error("Add project %s to hierarchy failed \n%s" % (project_id, r.content))
            return

        logger.info("Added project %s to hierarchy %s\n" % (project_id, self.id))
        print "Added project %s to hierarchy %s" % (project_id, self.id)

    def remove_included_project(self, project_id):
        if self.enable_as_optional:
            self.included_projects.discard(project_id)
            r = self.submit_included_projects()
        else:
            self.included_projects.discard(project_id)
            r = self.submit_included_projects()

        if r.status_code != 200:
            logger.error("Removed hierarchy failed %s\n %s" % (r.status_code, r.content))
            return

        logger.info("Removed project %s from hierarchy %s" % (project_id, self.id))
        print "Removed project %s from hierarchy %s" % (project_id, self.id)


    def submit_included_projects(self):
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "hierarchy": {key: value for key, value in self.__dict__.items() if value}
        }

        xml = dicttoxml(d, attr_type=False)

        root = ET.fromstring(xml)

        xslt_root = ET.parse('xslt/Submit_Workday_Project_Hierarchy.xslt')

        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        # Update hierarchy
        return requests.post(wd_cfg.get("wws", "url_resource_management"), data=string_result)