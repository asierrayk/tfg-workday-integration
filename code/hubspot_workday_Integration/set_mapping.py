import unicodecsv as csv
from modules.configuration import mapping
from hubspot.deal import Deal
from hubspot.company import Company
from modules.database import db

content = lambda x, y: x < y or y <= x
weak_content = lambda x, y: any(a in y for a in x) or any(a in x for a in y)


def map_hs_owner(mapping_file='tmp/mapping/positionid_emplid.csv'):
    with open(mapping_file, 'rb') as csvfile:
         spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
         next(spamreader, None)
         employee = []
         for row in spamreader:
             name, emplid, positionid, hiredate = row#map(lambda x: x.encode('utf-8'), row)
             employee.append({"name": name, "emplid": emplid, "positionid": positionid, "hiredate": hiredate})

    result = Deal.get_hubspot_owners()

    '''
    for e in employee:
        print " ".join(e["name"].split()[:2])

    print "-----------------"

    i = 0
    for o in result:
        i += 1
        print o["firstName"] + " " + o["lastName"]
    print i
    '''

    j = 0
    for o in result:
        full_name_owner = " ".join((o["firstName"] + " " + o["lastName"]).split()[:2])
        enc = False
        for e in employee:
            full_name = " ".join(e["name"].split()[:2])
            if full_name == full_name_owner:
                mapping.update("positionid_emplid", str(o["ownerId"]), e["emplid"] + ',' + e["positionid"])
                j += 1
                enc = True
        if not enc:
            print full_name_owner
    print j


def check_customer_mapping(mapping_file="tmp/mappings/Customers - HubSpot mapping - Customers.csv"):
    """
    Used to check if there is some customer in the pipeline that is not in hubspot
    :return:
    """


    companies = Company.get_all_companies()
    companies_ids = map(lambda x: str(x["companyId"]), companies)
    companies_unlinked = set(companies_ids)
    with open(mapping_file, 'rb') as csvfile:
         spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
         header = next(spamreader, None)
         mapped = []
         for row in spamreader:
             cust_id, descr, hubspot_id, _ = row
             mapped.append({"cust_id": cust_id, "descr": descr, "hubspot_id": hubspot_id})

    f = 0

    for m in mapped:
        if m["hubspot_id"] not in companies_ids:
            print "No mapeado"
            print m
            print "sugerencias"
            sug = 1
            for c in companies:
                try:
                    company_name = c["properties"]["name"]["value"].encode("utf8").lower()
                except:
                    company_name = ""
                try:
                    company_descr = c["properties"]["description"]["value"].encode("utf8").lower()
                except:
                    company_descr = ""
                descr =m["descr"].encode('utf8').lower() if "descr" in m else ""

                correcto = False
                if (company_name and weak_content(set(descr.split()), set(company_name.split()))) or (
                    company_descr and content(set(descr.split()), set(company_descr.split()))):
                    correcto = True

                if correcto:
                    print sug
                    sug += 1
                    print str(c["companyId"]) + ":" + company_name + ':' + company_descr
            print "\n"
            f += 1
        else:
            ix = companies_ids.index(m["hubspot_id"])
            companies_unlinked.remove(str(companies[ix]["companyId"]))
            try:
                company_name = companies[ix]["properties"]["name"]["value"].encode("utf8").lower()
            except:
                company_name = ""
            try:
                company_descr = companies[ix]["properties"]["description"]["value"].encode("utf8").lower()
            except:
                company_descr = ""
            descr = m["descr"].encode('utf8').lower() if "descr" in m else None
            if not descr:
                print m
                print "Mapeado, pero no comprobable. Sin descripcion"
                print "\n"
            else:
                correcto = False
                if (company_name and content(set(descr.split()), set(company_name.split()))) or (
                    company_descr and content(set(descr.split()), set(company_descr.split()))):
                        correcto = True

                if not correcto:
                    print "puede que este mapeo este mal, comprobar"
                    print m
                    print company_name + ": " + company_descr
                    print "\n"
    print f
    print companies_unlinked
    print len(companies_unlinked)

def check_deal_mapping(mapping_file="tmp/mappings/opps.csv"):
    hs_deals = Deal.get_all_deals()
    hs_deals_progress = [d for d in hs_deals if d.get("properties", {}).get("dealstage", {}).get("value") not in ["closedwon", "closedlost"]]


    with open(mapping_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        header = next(spamreader, None)
        pipe_opps = []
        for row in spamreader:
            practica, OPP, cliente, recurso, lider, probabilidad = row
            pipe_opps.append({"practica": practica, "OPP": OPP, "cliente": cliente,
                              "recurso": recurso, "lider": lider, "probabilidad": probabilidad})


    with open("output/check_deal_mapping.csv", 'wb') as csvfile:
        #csvfile.write("sep =,\n")
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        spamwriter.writerow(("dealid", "dealname", "company", "practice", "legal_entity", "dealstage", "project_status",
                             "opp_number", "owner_name", "owner_email", "error", "practice_pipe", "nombre_Oportunidad", "Customer_Manager", "Estado"))
        owners = {}
        for h in hs_deals_progress:
            company = next(iter(h.get("associations", {}).get("associatedCompanyIds", [])), None)
            practice = h.get("properties", {}).get("practice", {}).get("value")
            legal_entity = h.get("properties", {}).get("legal_entity", {}).get("value")
            dealstage = h.get("properties", {}).get("dealstage", {}).get("value")
            dealstage_verbose = mapping.get("dealstage_verbose",dealstage)
            project_status = mapping.get("projectstatus", dealstage)
            hs_opp_number = h.get("properties", {}).get("opp_number", {}).get("value")
            hubspot_owner_id = h.get("properties", {}).get("hubspot_owner_id", {}).get("value")
            if hubspot_owner_id in owners:
                ho = owners.get(hubspot_owner_id)
            else:
                ho = Deal.get_hubspot_owner(hubspot_owner_id)
                owners[hubspot_owner_id] = ho

            owner_name = ho["firstName"].encode("utf8") + ' ' + ho["lastName"].encode("utf8")
            owner_email = ho["email"]

            hs_opp_number = h.get("properties", {}).get("opp_number", {}).get("value")
            hs_practica = mapping.get("practicepipe", h.get("properties", {}).get("practice", {}).get("value"))

            if str(h["dealId"]) == "95984744":
                pass

            if hs_opp_number == "32" and hs_practica == "CLOUD":
                pass

            opp = next((x for x in pipe_opps if x["OPP"] == hs_opp_number and x["practica"].encode("utf-8") == hs_practica), {})


            try:
                pipe_opps.remove(opp)
            except Exception as e:
                pass

            if dealstage == "closedwon" or dealstage == "closedlost" or dealstage not in mapping.options("projectstatus"):
                continue

            status_prob = {
                "Active": ["100"],
                "Opportunity_Identified": ["10"],
                "Preparing_Proposal": ["20", "50"],
                "Proposal_Sent": ["45", "75"],
                "Closed_Lost": ["0"],
                "Contract_Sent": ["90"]
            }

            if not hs_opp_number:
                err_code = "Falta mapeo"
            elif not practice:
                err_code = "Falta practica en hubspot"
            elif not opp:
                err_code = "oportunidad no existente en el pipeline"
            elif opp.get("probabilidad") not in status_prob.get(project_status):
                err_code = "Estado incorrecto"
            else:
                err_code = ""

            practica = opp.get("practica")
            # bad format of the file "tmp/mappings/Verificacion Mapping HubSpot - Pipeline Data.csv"
            recurso = opp.get("recurso").encode('latin-1').decode('utf-8') if opp.get("recurso") else None
            lider = opp.get("lider").encode('latin-1').decode('utf-8') if opp.get("lider") else None
            probabilidad = opp.get("probabilidad")


            row = (h["dealId"],
                   h["properties"]["dealname"]["value"],
                   company,
                   practice,
                   legal_entity,
                   dealstage_verbose,
                   project_status,
                   hs_opp_number,
                   owner_name,
                   owner_email,
                   err_code,
                   practica,
                   recurso,
                   lider,
                   probabilidad
                   )
            spamwriter.writerow(row)

    with open("output/missed_in_hs.csv", 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        spamwriter.writerow(("practica", "OPP", "cliente", "recurso", "lider", "probabilidad"))
        for p in pipe_opps:
            if p["probabilidad"] in ["0", "100"]:
                continue
            try:
                spamwriter.writerow((p["practica"],
                                     p["OPP"],
                                     p["cliente"],
                                     p["recurso"].encode('latin-1').decode('utf-8'),
                                     p["lider"].encode('latin-1').decode('utf-8'),
                                     p["probabilidad"]))

            except Exception as e:
                print p
                print e

def generate_excluded():
    deals = Deal.get_all_deals()

    with open("output/excluded.csv", 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"')
        spamwriter.writerow(("excluded",))
        for d in deals:
            dealid = d.get("dealId")
            dealstage = d.get("properties", {}).get("dealstage", {}).get("value")
            if dealstage in ["closedwon", "closedlost"]:
                spamwriter.writerow((dealid,))



def load_customer_mapping(mapping_file="tmp/mappings/import/CONV_Customer.csv"):
    with open(mapping_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        header = next(spamreader, None)
        mapped = []
        for row in spamreader:
            cust_id, hubspot_id, _ = row
            mapped.append((hubspot_id, cust_id))
        l = [x[0] for x in mapped]
        print len(l) != len(set(l))
        s = set(l)
        for i in s:
            l.remove(i)
        print l


    db.insert_bulk("company_customer", mapped)

def load_excluded(mapping_file="tmp/mappings/import/excluded.csv"):
    with open(mapping_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(spamreader, None)
        mapped = []
        for row in spamreader:
            [excluded] = row
            mapped.append((excluded, ))

        l = list(mapped)
        print len(l) != len(set(l))
        s = set(l)
        for i in s:
            l.remove(i)
        print l


    db.insert_bulk("deals_excluded", mapped)


#TODO adjust to the file
def load_project_mapping(mapping_file="tmp/mappings/import/CONV_Projects.csv"):
    with open(mapping_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        header = next(spamreader, None)
        mapped = []
        for row in spamreader:
            project, deal, customer, project_name = row
            if deal == "":
                deal = None
            if project == "":
                project = None
            if not deal or not project:
                continue
            mapped.append((deal, project))
        l = [x[0] for x in mapped]
        print len(l) != len(set(l))
        s = set(l)
        for i in s:
            l.remove(i)
        print l


    db.insert_bulk("deal_project", mapped)


if __name__=="__main__":
    #map_hs_owner()
    #check_customer_mapping()
    #check_deal_mapping()
    load_customer_mapping()
    #load_project_mapping()
    #load_excluded("tmp/mappings/import/excluded.csv")
    #generate_excluded()
