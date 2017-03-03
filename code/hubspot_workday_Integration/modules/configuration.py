from ConfigParser import SafeConfigParser

class Configuration(SafeConfigParser):
    def __init__(self, filename):
        SafeConfigParser.__init__(self)
        self.filename = filename
        self.read(filename)

    def update(self, section, option, value):
        if not self.has_section(section):
            self.add_section(section)
        self.set(section, option, value)
        with open(self.filename, 'wb') as configfile:
            self.write(configfile)

    def get(self, section, option):
        try:
            return SafeConfigParser.get(self, section, option)
        except:
            return None

wd_cfg = Configuration('cfg/workday.ini')
hs_cfg = Configuration('cfg/hubspot.ini')
mapping = Configuration('cfg/mapping.ini')
mail_cfg = Configuration('cfg/mail.ini')




