import sqlite3
import unicodecsv as csv


class DataBase:
    """Makeshift database controller"""
    def __init__(self):
        self.conn = sqlite3.connect('db/integration_hubspot.db', check_same_thread=False)
        self.cur = self.conn.cursor()


        # Create table
        self.cur.execute('''CREATE TABLE IF NOT EXISTS deal_project
                        (
                        deal text primary key ON CONFLICT IGNORE not null ON CONFLICT IGNORE,
                        project text not null ON CONFLICT IGNORE
                         )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS company_customer
                        (
                        company text primary key ON CONFLICT IGNORE,
                        customer text not null
                        )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS deals_excluded
                        (
                        deal text primary key ON CONFLICT IGNORE
                        )''')

        self.conn.commit()

    def insert(self, table, value1, value2):

        # Insert a row of data
        try:
            if table == "deal_project":
                self.cur.execute("INSERT INTO deal_project VALUES (?,?)", (value1, value2))
            elif table == "company_customer":
                self.cur.execute("INSERT INTO company_customer VALUES (?,?)", (value1, value2))
            # Save (commit) the changes
            self.conn.commit()
            return True
        except:
            return False

    def insert_bulk(self, table, values):
        try:
            if table == "deal_project":
                self.cur.executemany("INSERT INTO deal_project VALUES (?,?)", values)
            elif table == "company_customer":
                self.cur.executemany("INSERT INTO company_customer VALUES (?,?)", values)
            elif table == "deals_excluded":
                self.cur.executemany("INSERT INTO deals_excluded VALUES (?)", values)
            else:
                return False
            # Save (commit) the changes
            self.conn.commit()
            return True
        except Exception as e:
            return False



    def get_project(self, deal):
        d = (deal,)
        self.cur.execute("SELECT project FROM deal_project WHERE deal=?", d)

        row = self.cur.fetchone()
        if row:
            return row[0]

        return None

    def get_deal(self, project):
        p = (project,)
        self.cur.execute("SELECT deal FROM deal_project WHERE project=?", p)

        row = self.cur.fetchone()
        if row:
            return row[0]

        return None

    def get_customer(self, company):
        c = (company,)
        self.cur.execute("SELECT customer FROM company_customer WHERE company=?", c)

        row = self.cur.fetchone()
        if row:
            return row[0]

        return None

    def is_excluded(self, deal):
        d = (deal,)
        self.cur.execute("SELECT deal FROM deals_excluded WHERE deal=?", d)

        row = self.cur.fetchone()
        if row:
            return row[0]

        return None

    def insert_excluded(self, value):
        try:
            self.cur.execute("INSERT INTO deals_excluded VALUES (?)", (value,))
            return True
        except:
            return False

    def __del__(self):
        self.conn.close()

    def export_db(self):
        # to export as csv file
        with open("output/export_deal_project.csv", "wb") as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            cursor = self.conn.cursor()
            for row in cursor.execute("SELECT * FROM deal_project"):
                # writeRow = ",".join(row)
                spamwriter.writerow(row)

        with open("output/export_company_customer.csv", "wb") as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            cursor = self.conn.cursor()
            for row in cursor.execute("SELECT * FROM company_customer"):
                spamwriter.writerow(row)

        with open("output/export_deals_excluded.csv", "wb") as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', lineterminator='\n')
            cursor = self.conn.cursor()
            for row in cursor.execute("SELECT * FROM deals_excluded"):
                spamwriter.writerow(row)

db = DataBase()



