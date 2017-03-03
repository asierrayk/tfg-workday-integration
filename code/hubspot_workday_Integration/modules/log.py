import logging


class Log:
    def __init__(self, logname, mode=logging.INFO):
        self.logger = logging.getLogger('myapp')
        hdlr = logging.FileHandler('./output/%s.log' % logname)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(mode)

logger = Log("app", logging.DEBUG).logger
