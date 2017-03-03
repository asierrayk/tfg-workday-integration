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
            #return
        print "valido"

        data = json.loads(web.data())
        print data
        subscritpionType = data[0]['subscriptionType']
        objectId = data[0]['objectId']
        appId = data[0]['appId']
        eventId = data[0]['eventId']
        occurredAt = data[0]['occurredAt']
        print appId

        logger.debug("POST APP RECEIVED \n" + str(data[0]))
        print subscritpionType
        if subscritpionType == "deal.creation":
            deal_creation(objectId)
        elif subscritpionType == "deal.propertyChange":
            if db.is_excluded(objectId):
                logger.warning("The deal received %s is excluded, and it'll not be updated to workday" % objectId)
                print "The deal received %s is excluded, and it'll not be updated to workday" % objectId
                return

            propertyChanged = data[0]["propertyName"]
            print propertyChanged
            logger.debug("deal.propertyChange %s", propertyChanged)
            deal_change(objectId, propertyChanged)



        logger.info("REQUEST PROCESSED")


# Maybe should be moved to another module
def valid_request():
    """
    To ensure that the requests you're getting at your webhook endpoint are actually coming from HubSpot,
    we populate a X-HubSpot-Signature header with a SHA-256 hash of the concatentation of the app-secret
    for your application and the request body we're sending.
    :param hubspot_signature:
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
    mail.send(mail_cfg.get("DEFAULT", "notify-to"), "Hubspot-Workday integration has finished", "Hubspot-Workday integration has finished")

def signal_handler(signal, frame):
    sys.exit(0)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # TODO remove comment
    #signal.signal(signal.SIGTSTP, signal_handler) # only valid in linux systems

    #init()
    app = web.application(urls, globals())
    app.run()

