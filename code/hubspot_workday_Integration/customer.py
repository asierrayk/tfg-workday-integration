import requests
from lxml import etree as ET
from modules.log import logger
from modules.configuration import wd_cfg
from modules.database import db

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Customer:
    '''
        Workday Object
    '''
    def __init__(self, id, name, company_id):
        self.id = id
        self.name = name
        self.company_id = company_id

    @classmethod
    def from_company(cls, company):
        id = db.get_customer(company.id)
        name = company.name
        company_id = company.id
        return cls(id, name, company_id)

    def submit(self):

        root = ET.Element("root")

        ET.SubElement(root, "user").text = wd_cfg.get("DEFAULT", "user")
        ET.SubElement(root, "password").text = wd_cfg.get("DEFAULT", "password")
        ET.SubElement(root, "tenant").text = wd_cfg.get("DEFAULT", "tenant")
        customer = ET.SubElement(root, "customer")
        ET.SubElement(customer, "name").text = self.name
        # ET.SubElement(customer, "id").text = str(self.companyId)


        xslt_root = ET.parse('xslt/Put_Customer.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")

        r = requests.post(wd_cfg.get("wws", "url_revenue_management"), data=string_result)
        print r.status_code
        print r.content

        reply_soap = ET.fromstring(r.content)
        wid, self.id = map(lambda x: x.text, reply_soap.findall('.//wd:ID', namespaces=nsd))

        if r.status_code != 200:
            logger.error("Submit_Customer failed %s\n %s" % (r.status_code, r.content))
            return False

        logger.warning("Customer submitted successfully. customer_ID %s" % self.id)
        print "Customer submitted successfully. customer_ID %s" % self.id

        #update database
        db.insert("company_customer", self.company_id, self.id)
        return True