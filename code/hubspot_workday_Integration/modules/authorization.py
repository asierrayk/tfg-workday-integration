import time, json, requests
from configuration import hs_cfg
from log import logger


class Authorization:
    def __init__(self, access_token=hs_cfg.get("authentication", "access_token"), refresh_token=hs_cfg.get("authentication", "refresh_token")):
        self.client_id = hs_cfg.get("DEFAULT", "client_id")
        self.client_secret = hs_cfg.get("DEFAULT", "client_secret")
        self.authorization_url = hs_cfg.get("urls", "authorization_url")

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = hs_cfg.get("authentication", "expires_at")
        self.code = None


        if self.check_token_expired():
            self.refresh()

    def get_code_and_token(self):
        print "Concede acceso al portal, y copia el code tras pinchar el link"
        print self.authorization_url

        self.code = raw_input('Pega el codigo \n')
        self.get_token()

    def get_token(self):
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {"grant_type": "authorization_code", "client_id": self.client_id, "client_secret": self.client_secret,
                "redirect_uri": "https://www.hubspot.com/", "code": self.code}

        r = requests.post("https://api.hubapi.com/oauth/v1/token", headers=headers, data=data)
        print r.status_code
        print r.content
        if r.status_code != 200:
            print r.content
            logger.warning("Invalid code")

        result = json.loads(r.content)

        self.access_token = result["access_token"]
        hs_cfg.update("authentication", "access_token", self.access_token)
        self.refresh_token = result["refresh_token"]
        hs_cfg.update("authentication", "refresh_token", self.refresh_token)
        self.expires_at = int(result["expires_in"]) + time.time()

    def info_access_token(self):
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}

        return requests.get("https://api.hubapi.com/oauth/v1/access-tokens/" + self.access_token, headers=headers)

    def info_refresh_token(self):
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}

        return requests.get("https://api.hubapi.com/oauth/v1/refresh-tokens/" + self.access_token, headers=headers)

    def check_token_expired(self):
        r = self.info_access_token()
        if r.status_code != 200:
            return True
        else:
            return False

    def is_token_expired(self):
        if time.time() > self.expires_at:
            return True
        else:
            return False

    def refresh(self):
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {"grant_type": "refresh_token", "client_id": self.client_id, "client_secret": self.client_secret,
                "redirect_uri": "https://www.hubspot.com/", "refresh_token": self.refresh_token}

        r = requests.post("https://api.hubapi.com/oauth/v1/token", headers=headers, data=data)
        print r.status_code
        print r.content

        if r.status_code != 200:
            self.get_code_and_token()
            return

        result = json.loads(r.content)
        self.access_token = result["access_token"]
        hs_cfg.update("authentication", "access_token", self.access_token)
        self.refresh_token = result["refresh_token"]
        hs_cfg.update("authentication", "refresh_token", self.refresh_token)
        self.expires_at = int(result["expires_in"]) + time.time()
        hs_cfg.update("authentication", "expires_at", str(self.expires_at))

hs_autho = Authorization()

