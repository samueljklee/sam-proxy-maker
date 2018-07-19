import boto3
import sys, os, random, time, datetime
import subprocess
import threading
import logging
import argparse

APIURL      = 'https://api.thegcloud.com'
APIKEY      = ''
APIHASH     = ''
REGION      = 'ord1'
SVRUSR      = 'proxy username'
SVRPSWD     = 'proxy password'
SVRPORT     = '3132'
LOGF        = "log.txt"
TIME        = time.strftime("%H%M%S",time.localtime())
#INFOF       = TIME+"-Info.txt"
DEBUG       = 0
global connect
global LOGGER
global INFO
global INFOF

class gigaThread (threading.Thread):
    def __init__(self, instanceID, cloudIP, cloudPSWD, serverPORT, serverUSR, serverPSWD):
      threading.Thread.__init__(self)
      self.instanceID = str(instanceID)
      self.cloudIP = str(cloudIP)
      self.cloudPSWD = str(cloudPSWD)
      self.serverPORT = str(serverPORT)
      self.serverUSR = str(serverUSR)
      self.serverPSWD = str(serverPSWD)

    def run(self):
        """ Execute commands to setup Squid on cloud machines """
        status = gigaApi().checkStatus(self.instanceID)
        while status == 4:
            """ Server not ready, wait for 25 - 30 seconds """
            timeout = random.randint(25,30)
            time.sleep(timeout)
            
            print("Cloud " + self.instanceID + " is not ready. Waiting for " + str(timeout) + " seconds.")
            LOGGER.info("Instance[" + self.instanceID +"] not ready. Status Code: "+ str(status) +". Waiting for " + str(timeout) + " seconds.")
            
            status = gigaApi().checkStatus(self.instanceID)

        if status == 0:
            print("Setting up Cloud(" + self.instanceID + ") ...")
            LOGGER.info("Instance[" + self.instanceID +"] Setting: " + self.cloudIP + ":" + self.serverPORT + ":" + self.serverUSR + ":" + self.serverPSWD)
            INFO.info(self.cloudIP + ":" + self.serverPORT + ":" + self.serverUSR + ":" + self.serverPSWD)
            
            command = "sshpass -p " + self.cloudPSWD + 
                " ssh -o StrictHostKeyChecking=no root@" + self.cloudIP + 
                " 'yum install wget -y && wget https://raw.githubusercontent.com/samueljklee/ProxyMaker/master/data/setup.sh && yum update openssl -y && sed -i \"s/hello/" + 
                self.serverUSR + "/g\" setup.sh && sed -i \"s/world/" + 
                self.serverPSWD + "/g\" setup.sh && sed -i \"s/65002/" + 
                self.serverPORT + "/g\" setup.sh && chmod +x setup.sh && source setup.sh' "

            subprocess.run(command, shell=True)
            
            LOGGER.info("Instance[" + self.instanceID +"] threading completed.")
        else:
            print("Cloud(" + self.instanceID +") is off. Skipping ...")

def getInfoFileName():
    return time.strftime("%H%M%S",time.localtime())+"-Info.txt"

class LOGGING:
    global INFOF
    LogFile     = LOGF
    InfoFile    = getInfoFileName()
    INFOF       = InfoFile

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

class gigaApi:
    @staticmethod
    def checkStatus(instanceID):
        """ 
        InstanceState code: 
        0 - on
        3 - off
        4 - unknown
        """
        status = connect.describe_instance_status(InstanceIds=[instanceID])

        return status['InstanceStatuses'][0]['InstanceState']['Code']

    @staticmethod
    def getInstance():
        """
        Describe Instance Type
        @returns: all instances
        +------------+-----------+-------+------+
        | name | cpu_cores | mem | disk |
        +------------+-----------+-------+------+
        | gcl.1 | 1 | 1024 | 30 |
        | gcl.2 | 1 | 2048 | 60 |
        | gcl.4 | 2 | 4096 | 90 |
        | gcl.8 | 4 | 8192 | 120 |
        | gcl.core.2 | 2 | 2048 | 60 |
        | gcl.core.4 | 4 | 4096 | 90 |
        | gcl.core.8 | 8 | 8192 | 180 |
        | gcl.max.8 | 2 | 8192 | 180 |
        | gcl.max.16 | 4 | 16384 | 360 |
        +------------+-----------+-------+------+
        """
        inst = "gcl.1"
        return inst

    @staticmethod
    def getImage():
        """ 
        Get available images q
        @returns: all images
        """
        #images = connect.describe_images()
        #centos = images['Images']
        image = "centos64_7"
        return image

    @staticmethod
    def createCloud(image,instance,REGION):
        """
        Run instances
        @param: ImageId, InstanceType, MinCount, MaxCount
        @output: instanceId, publicIpAddress
        """
        timeout = random.randint(3,7)
        print("[" + str(datetime.datetime.now()) + "] Creating cloud[" + str(instance) +"] in " + str(timeout) + " seconds ...")
        LOGGER.info("Creating cloud[" + str(instance) +"] in " + str(timeout) + " seconds ...")
        time.sleep(timeout)

        ### Check retries, if reach max, exit thread
        ### 'ResponseMetadata': {'RetryAttempts': 0}
        server = connect.run_instances(ImageId=image, InstanceType=instance, MinCount=1, MaxCount=1, Placement={'AvailabilityZone':REGION})
        LOGGER.info(str(server))


        if DEBUG: print(server)

    @staticmethod
    def getInstanceIDIP(instanceIdList, publicIpAddressList):
        """ 
        Get all available instances in account
        - Store IP and Instance Id to lists
        @returns: PublicIpAddress, Instance Id ["Reservations"]['Instances'][InstanceId]
        """   
            
        instance = connect.describe_instances()

        for i in range(len(instance['Reservations'][0]['Instances'])):
            if instance['Reservations'][0]['Instances'][i]['Platform'] != 'Win16':
                instanceIdList.append(instance['Reservations'][0]['Instances'][i]['InstanceId'])
                publicIpAddressList.append(instance['Reservations'][0]['Instances'][i]['PublicIpAddress'])
        
        LOGGER.info("Instance ID    : " + str(instanceIdList))
        LOGGER.info("IP Address     : " + str(publicIpAddressList))
            
    @staticmethod
    def getPassword(pswdList, instanceIdList):
        """
        Get password
        @param: InstanceId
        @returns: password
        """
        for i in range(len(instanceIdList)):
            pswd = connect.get_password_data(InstanceId=instanceIdList[i])
            pswdList.append(pswd['PasswordData'])
        
        LOGGER.info("Cloud Password : " + str(pswdList))

    @staticmethod
    def print(instanceIdList, publicIpAddressList, pswdList):
        for i in range(len(instanceIdList)):
            print("Instance(" + str(instanceIdList[i]) +"): IP: " + str(publicIpAddressList[i]) + " Password: " + str(pswdList[i]) + "  Status: " + str(gigaApi().checkStatus(instanceIdList[i])) + ".")
            LOGGER.info("Instance(" + str(instanceIdList[i]) +"): IP: " + str(publicIpAddressList[i]) + " Password: " + str(pswdList[i]) + "  Status: " + str(gigaApi().checkStatus(instanceIdList[i])) + ".")

    @staticmethod
    def destroy(instanceIdList):
        """
        print("Stopping Instance " + str(instanceIdList) + " ..." )
        connect.stop_instances(InstanceIds=instanceIdList)
        """
        print("Terminating Instances " + str(instanceIdList) + " ..." )
        LOGGER.info("Terminating Instances " + str(instanceIdList) + " ..." )
        connect.terminate_instances(InstanceIds=instanceIdList)

def create(numServer, createNewServer, region):
    """ Variables """
    publicIpAddressList = list()
    instanceIdList = list()
    pswdList = list()
    machines = list()
    """ Get Instance and Image """
    instance = gigaApi().getInstance()
    image = gigaApi().getImage()

    if createNewServer:
        for _ in range(numServer):
            """ Create cloud server """
            gigaApi().createCloud(image,instance, region)
    
    """ Update instanceIdList and publicIpAddressList """
    gigaApi().getInstanceIDIP(instanceIdList, publicIpAddressList)

    """ Update password of cloud servers """
    gigaApi().getPassword(pswdList, instanceIdList)
    
    """ Setup for threading """
    [machines.append("cloud"+str(i)) for i in range(len(instanceIdList))]   

    """ Initialize threads names """
    for i in range(0,len(machines)):
        machines[i] = gigaThread(instanceIdList[i], publicIpAddressList[i], pswdList[i], SVRPORT, SVRUSR, SVRPSWD)
    
    """ Start threads """
    for i in range(0,len(machines)):
        machines[i].start()

    """ Wait for threads to terminate """
    for i in range(0,len(machines)):
        machines[i].join()
    
    print("\n\n\nCreation success :)")
    
    return 1

def getInfo():
    """ Variables """
    publicIpAddressList = list()
    instanceIdList = list()
    pswdList = list()

    gigaApi().getInstanceIDIP(instanceIdList, publicIpAddressList)
    gigaApi().getPassword(pswdList, instanceIdList)
    gigaApi().print(instanceIdList, publicIpAddressList, pswdList)

def terminate():
    """ Variables """
    publicIpAddressList = list()
    instanceIdList = list()

    gigaApi().getInstanceIDIP(instanceIdList, publicIpAddressList)
    gigaApi().destroy(instanceIdList)

def gigaApiInit(REGIONAPI='ord1', APIKEYAPI=APIKEY, APIHASHAPI=APIHASH):
    global connect
    global INFO
    global LOGGER
    global REGION
    INFO = LOGGING().infoLog(APIKEYAPI)
    LOGGER = LOGGING().loggingLog('Logging File')

    if REGIONAPI == "":
        REGION = 'ord1'
    else:
        REGION = REGIONAPI

    session = boto3.session.Session()
    connect = session.client('ec2',
                    endpoint_url=APIURL,
                    aws_access_key_id=APIKEYAPI,
                    aws_secret_access_key=APIHASHAPI,
                    region_name=REGIONAPI)

def gigaApiCreate(numServer, REGION):
    return create(int(numServer), True, REGION)

def gigaApiInfo():
    create(0, False, REGION)
    getInfo()

def gigaApiDestroy():
    terminate()

def gigaApiReturnFileName():
    """ Return names of Log File and Info File """
    global INFOF
    return LOGF, INFOF

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    actionParser = parser.add_mutually_exclusive_group()
    actionParser.add_argument("--create", help="Create servers.", action="store_true")
    actionParser.add_argument("--update", help="Update servers.", action="store_true")
    actionParser.add_argument("--info", help="Information of servers. ", action="store_true")
    actionParser.add_argument("--terminate", help="Terminate servers. ", action="store_true")
    actionParser.add_argument("--clean", help="Remove .txt files. ", action="store_true")
    
    optionalNumServers = parser.add_mutually_exclusive_group()
    optionalNumServers.add_argument("-n", "--numServers", type=int, nargs=1, help="Number of proxies", default=1)
    
    optionalRegion = parser.add_mutually_exclusive_group()
    optionalRegion.add_argument("-r", "--region", type=str, nargs=1, help="Region (ord1 | lax1)", default="ord1")

    args = parser.parse_args()
    
    INFO = LOGGING().infoLog('Info File')
    LOGGER = LOGGING().loggingLog('Logging File')


    if args.create:
        print("[" + str(datetime.datetime.now()) + "] Creating ...")
        LOGGER.info("Creating ...")

        if args.numServers[0] <= 0:
            print("Check arguments.")
            LOGGER.error("Check arguments. Exiting ...")
            sys.exit(0)
        else:
            numServer = args.numServers[0]
        
        if len(args.region) <= 0:
            print("Check arguments.")
        else:
            REGION = args.region[0]

        print("APIURL: {}\nAPIKEY: {}\nREGION: {}".format(APIURL, APIKEY, REGION))

        connect = boto3.client('ec2',
                    endpoint_url=APIURL,
                    aws_access_key_id=APIKEY,
                    aws_secret_access_key=APIHASH,
                    region_name=REGION)
        
        create(numServer, True, REGION)

    # If not create
    connect = boto3.client(
                    'ec2',
                    endpoint_url=APIURL,
                    aws_access_key_id=APIKEY,
                    aws_secret_access_key=APIHASH,
                    region_name=REGION)

    if args.update:
        LOGGER.info("Updating ...")
        create(0, False, REGION)

    elif args.info:
        print("Getting info ...")
        LOGGER.info("Getting info ...")
        getInfo()

    elif args.terminate:
        print("Terminating ...")
        LOGGER.info("Terminating ...")
        terminate()
    elif args.clean:
        print("Cleaning all .txt files.")
        os.system("rm *.txt")

    else:
        print("\nArguments required: [Action] [Optional] [Region]") 
        print("		Action: --create | --update | --info | --terminate") 
        print("		Optional: -n (number of servers) -r (region)")
        print("		--help\n")