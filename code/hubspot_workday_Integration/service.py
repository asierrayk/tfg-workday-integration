import hashlib
import json
import web
import atexit, sys
import signal

from modules import mail
from handler import *
from modules.configuration import hs_cfg, mail_cfg

urls = (
	'/', 'index'
)



class index:
    def POST(self):
        if not valid_request():
            logger.warning("A request unauthorized has been received from IP %s" % web.ctx.env["REMOTE_ADDR"])
            logger.warning(web.data())
            print "A request unauthorized has been received from IP %s" % web.ctx.env["REMOTE_ADDR"]
            print web.data()
            # TODO
            return


        data = json.loads(web.data())
        subscritpionType = data[0]['subscriptionType']
        objectId = data[0]['objectId']
        appId = data[0]['appId']
        eventId = data[0]['eventId']
        occurredAt = data[0]['occurredAt']

        print "Authorized request received: %s" % subscritpionType
        logger.info("AUTHORIZED REQUEST RECEIVED \n" + str(data[0]))

        if db.is_excluded(objectId):
            logger.warning("The deal received %s is excluded, and it'll not be uploaded to workday" % objectId)
            print "The deal received %s is excluded, and it'll not be uploaded to workday" % objectId
            return


        print subscritpionType
        if subscritpionType == "deal.creation":
            deal_creation(objectId)
        elif subscritpionType == "deal.propertyChange":
            propertyChanged = data[0]["propertyName"]
            deal_change(objectId, propertyChanged)




# Maybe should be moved to another module
def valid_request():
    """
    To ensure that the requests you're getting at your webhook endpoint are actually coming from HubSpot,
    we populate a X-HubSpot-Signature header with a SHA-256 hash of the concatentation of the app-secret
    for your application and the request body we're sending.
    :return:
    """
    signature = hashlib.sha256(hs_cfg.get("DEFAULT", "client_secret") + web.data()).hexdigest()
    try:
        request_signature = web.ctx.environ["HTTP_X_HUBSPOT_SIGNATURE"]
        return signature == request_signature
    except:
        return False


@atexit.register
def goodbye():
    print "send mail"
    mail.send(mail_cfg.get("DEFAULT", "notify-to"), mail_cfg.get("service-finished", "subject"), mail_cfg.get("service-finished", "content"))

def signal_handler(signal, frame):
    sys.exit(0)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # TODO uncomment SIGSTP signal
    signal.signal(signal.SIGTSTP, signal_handler) # only valid in linux systems

    #init()
    app = web.application(urls, globals())
    app.run()

