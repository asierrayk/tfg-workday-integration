from lxml import etree



def dict_to_xml(dic, root=None, parent=None):
    if parent is not None:
        r = etree.SubElement(parent, root)
    elif root is not None:
        r = etree.Element(root)
    else:
        return

    for d in dic:
        if isinstance(dic[d], dict):
            dict_to_xml(dic[d], d, r)
        elif dic[d]:
            etree.SubElement(r, d).text = dic[d]

    return r


'''
        root = ET.Element("root")
        ET.SubElement(root, "user").text = wd_cfg.get("DEFAULT", "user")
        ET.SubElement(root, "password").text = wd_cfg.get("DEFAULT", "password")
        ET.SubElement(root, "tenant").text = wd_cfg.get("DEFAULT", "tenant")
        project = ET.SubElement(root, "project")
        ET.SubElement(project, "name").text = self.dealname
        ET.SubElement(project, "id").text = self.dealId
'''
if __name__ == "__main__":


    print ET.tostring(root, method="html")