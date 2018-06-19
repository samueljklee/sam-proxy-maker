import sys, time
import logging

proxy   = "sal146-us"
domain  = ".netnut.io"
port    = "33128"
USR     = "netnut username"
PSWD    = "netnut password"

global LOGF
global INFOF
TIME        = time.strftime("%H%M%S",time.localtime())
LOGF        = "log.txt"
INFOF       = TIME+"-Info.txt"

class LOGGING:
    LogFile     = LOGF
    InfoFile    = INFOF

    def infoLog(self,name):
            """ 
                Store IP:PORT:USER:PASS 
            """
            formatter = logging.Formatter(fmt='%(message)s')
            handler = logging.FileHandler(self.InfoFile,mode='w')
            handler.setFormatter(formatter)
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            return logger

    def loggingLog(self,name):
        """ 
            Logging 
        """
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.FileHandler(self.LogFile,mode='w')
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        return logger

def nnApiInit():
    global INFO
    global LOGGER
    INFO = LOGGING().infoLog('Info File')
    LOGGER = LOGGING().loggingLog('Logging File')

    LOGGER.info("Creating Netnut Proxies ...")
    print("Start:")

def nnApiCreate(number, username, password):
    global INFO
    global LOGGER

    for i in range(0,int(number)):
        result = proxy + str(i+1) + domain + ":" + port + ":" + str(username) + ":" + str(password)
        LOGGER.info("Created proxy:" + result)
        INFO.info(result)

    LOGGER.info("Successful creation :)")
    print("NN Done.")
    time.sleep(10)
    return 1

def nnApiReturnFileName():
    global INFO
    global LOGGER
    """ Return names of Log File and Info File """
    return LOGF, INFOF 

if __name__ == "__main__":
    print("NetNut")
    apiCreate(10, USR, PSWD)