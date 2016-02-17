import datetime
import time
import threading
import traceback
import logging

class Scheduler(threading.Thread):
    def __init__(self, action, cycleTime=datetime.timedelta(minutes=10),
                 threadName="ScheduledThread", silent=True):
        # Needed to avoid "Thread.__init__() not called"
        # i.e. calls Thread.__init__()
        super(Scheduler, self).__init__()

        self.lastRun = datetime.datetime.now()
        self.action = action
        self.cycleTime = cycleTime

        self.name = threadName
        self.silent = silent
        self.stop = threading.Event()
        self.force = False

    def timeLeft(self):
        """
        Check how long we have until we run again
        :return: timedelta
        """
        if self.isAlive():
            logging.info("Is Alive")
            return self.cycleTime - (datetime.datetime.now() - self.lastRun)
        else:
            logging.info("Not Alive")
            return datetime.timedelta(seconds=0)
            
    def forceRun(self):
        if not self.action.amActive:
            self.force = True
            return True
        return False

    def run(self):
        """
        Runs the thread
        """
        try:
            while not self.stop.is_set():
                current_time = datetime.datetime.now()
                should_run = False
                
                # check if interval has passed
                if current_time - self.lastRun >= self.cycleTime:
                    should_run = True

                if should_run:
                    self.lastRun = current_time
                    #if not self.silent:
                    logging.info("Starting new thread: " + self.name)
                    self.action.run(self.force)
                else:
                    logging.debug("Not starting new thread: " + self.name)

                if self.force:
                    self.force = False

                time.sleep(1)
            # exiting thread
            self.stop.clear()
        except:
            logging.exception("Got an exception:")
            raise
