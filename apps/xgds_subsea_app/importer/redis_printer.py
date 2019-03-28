import sys
import redis
import threading
from time import sleep
from redis_utils import TelemetryQueue


class TelemetryPrinter:
    def __init__(self,channel_name):
        self.channel_name = channel_name
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        print '%s listener started' % self.channel_name
        tq = TelemetryQueue(self.channel_name)
        for msg in tq.listen():
            print '%s: %s' % (self.channel_name, msg)

if __name__=='__main__':
    channel_names = sys.argv[1:]
    for channel_name in channel_names:
        TelemetryPrinter(channel_name)

    while True:
        sleep(1)
