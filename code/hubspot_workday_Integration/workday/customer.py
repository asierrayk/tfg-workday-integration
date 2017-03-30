import requests
from lxml import etree as ET
from modules.log import logger
from modules.configuration import wd_cfg
from modules.database import db
from dicttoxml import dicttoxml

nsd = {'env': 'http://schemas.xmlsoap.org/soap/envelope/',
               'wd': 'urn:com.workday/bsvc'}

class Customer:
    '''
        Workday Object representing a customer
    '''
    def __init__(self, id, name, company_id):
        self.id = id
        self.name = name
        self.company_id = company_id

    @classmethod
    def from_company(cls, company):
        """
        Constructor from a HubSpot company
        :param company:  HubSpot company
        :return:
        """
        id = db.get_customer(company.id)
        name = company.name
        company_id = company.id
        return cls(id, name, company_id)

    def submit(self):
        """
        Submit the Customer to Workday
        :return:
        """
        d = {
            "user": wd_cfg.get("DEFAULT", "user"),
            "password": wd_cfg.get("DEFAULT", "password"),
            "tenant": wd_cfg.get("DEFAULT", "tenant"),
            "customer": {key: value for key, value in self.__dict__.items() if value}
        }

        xml = dicttoxml(d, attr_type=False)
        root = ET.fromstring(xml)


        xslt_root = ET.parse('xslt/Put_Customer.xslt')
        transform = ET.XSLT(xslt_root)
        result = transform(root)
        string_result = ET.tostring(result, method="html")


        r = requests.post(wd_cfg.get("wws", "url_revenue_management"), data=string_result)

        if r.status_code != 200:
            logger.warning("Submit_Customer failed %s\n %s" % (r.status_code, r.content))
            print "Submit_Customer failed %s" % r.status_code
            return False

        reply_soap = ET.fromstring(r.content)

        ids = reply_soap.find('.//wd:Put_Customer_Response/wd:Customer_Reference', namespaces=nsd)
        wid = ids.find('wd:ID[@wd:type="WID"]', namespaces=nsd).text
        try:
            cust_ref_id = ids.find('wd:ID[@wd:type="Customer_Reference_ID"]', namespaces=nsd).text
        except:
            cust_ref_id = None
        self.id = ids.find('wd:ID[@wd:type="Customer_ID"]', namespaces=nsd).text

        #update database
        db.insert("company_customer", self.company_id, self.id)
        logger.info("Customer submitted successfully. customer_ID %s, company_id %s" % (self.id, self.company_id))

        print "Customer submitted successfully. customer_ID %s" % self.id
        return True
