import datetime

class Logger:
    @staticmethod
    def info(msg):
        print(datetime.datetime.now(), str(msg))
    