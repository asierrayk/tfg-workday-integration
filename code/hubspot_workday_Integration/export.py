from hubspot.deal import Deal
from hubspot.company import Company
from modules.database import db
import datetime

dt = datetime.datetime.now().strftime('%d_%m_%Y__%H_%M')
Deal.export_all_deals('output/all_deals_' + dt + '.csv')
Company.export_all_companies('output/all_companies' + dt + '.csv')
db.export_db()

