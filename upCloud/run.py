import os, sys, time, string, random
import requests, base64, json
import logging
import tempfile
import argparse

TIME    = time.strftime("%H%M%S",time.localtime())
LOGF    = "log.txt"
INFOF   = TIME+"-Info.txt"
BCKUPF  = "backup-Info.txt"
USR     = "upcloud username"
PSWD    = "upcloud password"
SVRUSR  = "server username"
SVRPSWD = "server password"
SVRPORT = 3128

class LOGGING:
    LogFile     = LOGF
    InfoFile    = INFOF
    BackupFile  = BCKUPF

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

    def backupLog(self,name):
        """ 
            Store UUID:PORT 
        """
        formatter = logging.Formatter(fmt='%(message)s')
        handler = logging.FileHandler(self.BackupFile,mode='w')
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        return logger

class BASEAPI:
    credentials = USR + ":" + PSWD
    api = "https://api.upcloud.com/"
    api_v = "1.2"
    token = base64.b64encode(credentials.encode())
    USER = SVRUSR
    PASS = SVRPSWD
    PORT = SVRPORT
    ### 12173-12299
    SVRCNT = 1
    NUMSERVER = 0
    setOfUUID = set()
    uuidToPort = dict()     ### uuidToPort NOT IN USE. Future?

    def getAccount(self, endpoint):
        """ 
            Get Account Information 
        """
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        conn = requests.get(url, headers=headers)
        ready = self.checkResponse(conn)
        if not ready:
            LOGGER.info("UNAUTHORIZED_ADDRESS")
            sys.exit(0)

    def createServer(self, endpoint):
        """ 
            Create Server 
        """
        ready = False
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json" 
        }
        data = {
            "server": {
                "zone": "us-chi1",
                "title": "Chicago Server " + str(self.SVRCNT),
                "hostname": "server.booyah.com",
                "plan": "1xCPU-1GB",
                "user_data": "#!/bin/bash\nyum install squid wget httpd-tools -y\ntouch /etc/squid/passwd\nhtpasswd -b /etc/squid/passwd " + self.USER + " " + self.PASS + " \nwget -O /etc/squid/squid.conf https://raw.githubusercontent.com/samueljklee/ProxyMaker/master/data/setup.conf --no-check-certificate \n sed -i \"s/3128/" + str(self.PORT) + "/g\" /etc/squid/squid.conf \ntouch /etc/squid/blacklist.acl\nsystemctl restart squid.service\nsystemctl enable squid.service\niptables -I INPUT -p tcp --dport " + str(self.PORT) + " -j ACCEPT\niptables-save",
                "storage_devices": {
                    "storage_device": [
                        {
                            "action": "clone",
                            "title": "CentOS Template",
                            "storage": "01000000-0000-4000-8000-000050010300",
                            "tier": "maxiops"
                        }
                    ]
                },
                "login_user": {
                    "username": "root",
                }
            }
        }
        LOGGER.info("Sending request to create server ...")
        while not ready:
            conn = requests.post(url, headers=headers, data=json.dumps(data))
            ready = self.checkResponse(conn)        
        
        res = conn.json()
        
        # Store UUID to PORT and store it to BackupLog
        self.uuidToPort[res["server"]["uuid"]] = self.PORT
        BACKUP.info(str(res["server"]["uuid"]) + ":" + str(self.PORT))

        #self.PORT += 1
        self.SVRCNT += 1

        LOGGER.info("Create Servers Successful. :)")

    ### Zone

    ### Plan

    ### Storage

    def getStorageUUID(self, endpoint):
        """ 
            Get Storage UUID 
        """
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        conn = requests.get(url, headers=headers)
        res = conn.json()
        server = res["storages"]["storage"]
        self.NUMSERVER = len(server)
        LOGGER.info(str(self.NUMSERVER) + " storages found!")
        
        for i in range(len(server)):
            # Store Storage UUID into temporary file
            if server[i]["license"] == 0 and server[i]["size"] == 10:
                # Store UUID into temporary file
                storageFP.write(bytes(server[i]["uuid"]+"\n", encoding="utf-8"))
                LOGGER.info("UUID: " + str(server[i]["uuid"]))
            else:
                LOGGER.info("STORAGE of Hidden Server: " + str(server[i]["uuid"]))

    def getUUID(self, endpoint):
        """ 
            Get Server UUID 
            Update uuidToPort
        """
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        conn = requests.get(url, headers=headers)
        res = conn.json()
        server = res["servers"]["server"]
        self.NUMSERVER = len(server)
        LOGGER.info(str(self.NUMSERVER) + " servers found!")
        
        for i in range(len(server)):
            # In case server for hidden
            ### check if it's server.booyah.com instead
            if server[i]["hostname"] != "hidden":
                # Store UUID into temporary file
                uuidFP.write(bytes(server[i]["uuid"]+"\n", encoding="utf-8"))
                self.setOfUUID.add(server[i]["uuid"])
                LOGGER.info("UUID: " + str(server[i]["uuid"]))
            else:
                LOGGER.info("UUID of Hidden Server: " + str(server[i]["uuid"]))
        
        # State: ran create function but crashes before firewallUpdate
        # If not using --create, but ran beforehand.
        # --debug -d firewall/ip
        # Reconstruct self.uuidToPort using BackupLog File
        if len(self.uuidToPort) == 0 and os.stat(BCKUPF).st_size != 0: 
            readBackupLog = open(BCKUPF,"r")
            for line in readBackupLog:
                splitLine = line.split(":")
                self.uuidToPort[splitLine[0]] = splitLine[1].strip("\n")
        
    '''
    Update Firewall Rules
    '''
    def firewallUpdate(self, endpoint, fendpoint):
        uuidFP.seek(0)
        LOGGER.info("Updating Firewall ...")
        for line in uuidFP:
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint + "/" + uuid + fendpoint
            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            # Incoming Traffic
            ### for uuid not in uuidToPort FIX
            data = {
                "firewall_rule": {
                    "action": "accept",
                    "comment": "Allow incoming traffic.",
                    "direction": "in",
                    "family": "IPv4",
                    "protocol": "tcp",
                    "destination_port_end": str(self.PORT), # str(self.uuidToPort[uuid]),
                    "destination_port_start": str(self.PORT), #str(self.uuidToPort[uuid]),

                }
            }
    
            ready = False
            while not ready:
                conn = requests.post(url, headers=headers, data=json.dumps(data))
                ready = self.checkResponse(conn)
                if ready == False:
                    timeout = random.randint(30,60)
                    LOGGER.warning("Server is not ready. Timeout for  " + str(timeout) + " seconds." )
                    time.sleep(timeout)
                else:
                    LOGGER.info("Server is ready. Updating Firewall." )

            # Outgoing Traffic
            data = {
                "firewall_rule": {
                    "action": "accept",
                    "comment": "Allow outgoing traffic.",
                    "direction": "out",
                    "family": "IPv4",
                    "protocol": "tcp",
                    "source_port_end": str(self.PORT), # str(self.uuidToPort[uuid]),
                    "source_port_start": str(self.PORT), # str(self.uuidToPort[uuid]),
                }
            }

            conn = requests.post(url, headers=headers, data=json.dumps(data))
            self.checkResponse(conn)     

        LOGGER.info("Update Firewall Successful. :)")    

    '''
    Stop Server, Destroy Server, Destroy Storage
    '''
    ### if can't find server more than X times, skip it (due to manually stopping and deleting X server)
    def destroy(self, endpoint, endpoint1, endpoint2):
        uuidFP.seek(0)
        LOGGER.info("Stopping servers ...")
        for line in uuidFP:
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint + "/" + uuid + endpoint1
            checkUrl = self.api + self.api_v + endpoint + "/" + uuid
            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            conn = requests.get(checkUrl, headers=headers)
            req = conn.json()

            if req["server"]["state"] != "stopped":
                conn = requests.post(url, headers=headers)
                self.checkResponse(conn)
    
                LOGGER.info("Stopping UUID: " + str(uuid))  
            else:
                LOGGER.info("UUID: " + str(uuid) + " is already stopped. Skipping ...") 

        LOGGER.info("Destroying servers ...")
        uuidFP.seek(0)
        for line in uuidFP:
            ready = False
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint + "/" + uuid

            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            while not ready:
                conn = requests.delete(url, headers=headers)
                ready = self.checkResponse(conn)
                if ready == False:
                    timeout = random.randint(30,60)
                    LOGGER.warning("UUID: " + str(uuid) + " not ready. Timeout for " + str(timeout) + " seconds.")
                    time.sleep(timeout)
                else:
                    LOGGER.info("Success destroyed UUID: " + str(uuid))
        
        LOGGER.info("Destroying storages ...")
        storageFP.seek(0)
        for line in storageFP:
            ready = False
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint2 + "/" + uuid

            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            while not ready:
                conn = requests.delete(url, headers=headers)
                ready = self.checkResponse(conn)
                if ready == False:
                    timeout = random.randint(30,60)
                    LOGGER.info("Storage UUID: " + str(uuid) + " not ready. Timeout for " + str(timeout) + " seconds.")
                    time.sleep(timeout)
                else:
                    LOGGER.info("Success destroyed storage UUID: " + str(uuid))

            LOGGER.info("Destroying Storage UUID: " + str(uuid) + ".")  
        
        LOGGER.info("Destroy Successful. :)")

    '''
    Get IP address
    '''
    ### Check if it's not proxy server
    def getIP(self, endpoint, endpoint1, endpoint2):
        LOGGER.info("Finding IP Address ...")
        
        url = self.api + self.api_v + endpoint2
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        
        conn = requests.get(url, headers=headers)
        self.checkResponse(conn)
        res = conn.json()
        servers = res["ip_addresses"]["ip_address"]

        uuidFP.seek(0)
        for line in uuidFP:
            tempUUID = str(line,encoding="utf-8").strip("\n")

            for i in range(len(servers)):
                if servers[i]["server"] == tempUUID and servers[i]["family"] == "IPv4" and servers[i]["access"] == "public":
                    ip = servers[i]["address"]

                    LOGGER.info("IP:PORT:USER:PASS: " + ip + ":" + str(self.PORT) + ":" + self.USER + ":" + self.PASS)                
                    INFO.info(ip + ":" + str(self.PORT) + ":" + self.USER + ":" + self.PASS)
                    

    '''
    Check Server Status
    '''
    def getStatus(self, endpoint):
        uuidFP.seek(0)
        LOGGER.info("Checking servers ...")
        for line in uuidFP:
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint + "/" + uuid
            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            conn = requests.delete(url, headers=headers)
            self.checkResponse(conn)

    '''
    Compute request responds
        200 - OK
        201 - Created
        202 - Accepted
        204 - No Content - json doesn't return anything
    '''
    def checkResponse(self, res):
        if str(res) == "<Response [200]>" or str(res) == "<Response [201]>" or str(res) == "<Response [202]>":
            LOGGER.info("Command Successful. " + str(res.json()))
            return True
        elif str(res) == "<Response [204]>":
            LOGGER.info("Command Successful.")
            return True
        data = res.json()
        LOGGER.info(str(data))
        key = list(data.keys())
        ### if AUTHENTICATION_FAILED
        if key[0] == 'error' :
            LOGGER.error("Error Code: " + data['error']['error_code'])
            if data['error']['error_code'] == "SERVER_STATE_ILLEGAL":
                return False
            elif data['error']['error_code'] == "UNAUTHORIZED_ADDRESS":
                LOGGER.error("Unauthorized Address. Please update your IP into your UpCloud's setting.")
                print("Exiting ... Check Log File For Error ...")
                sys.exit(0)
            elif data['error']['error_code'] == "FIREWALL_RULE_EXISTS":
                return True
            elif data['error']['error_code'] == "SERVER_CREATING_LIMIT_REACHED":
                print("Limit Reached. Waiting for 30 minutes ...")
                LOGGER.warning("Waiting for 30 Minutes.")
                time.sleep(1800)
                return False
        else:
            LOGGER.info("Data: " + str(data))  
            print(data)
        

class ACCOUNT(BASEAPI):
    # Check connection
    def check(self):    
        endpoint = "/account"
        self.getAccount(endpoint)
    
    # Create server
    def create(self, numProx):
        endpoint = "/server"
        endpoint1 = "/firewall_rule"
        endpoint2 = "/ip_address"
        proxyCnt = 1

        while proxyCnt <= numProx:
            LOGGER.info("Creating Proxy " + str(proxyCnt) + " ...")
            self.createServer(endpoint)

            if proxyCnt % 10 == 0:
                # 3 minutes - 12 minutes
                timeout = random.randint(180,720)
            else:
                timeout = random.randint(0,3)
                
            proxyCnt += 1
            LOGGER.info("Creating Server ... Timeout for " + str(timeout) + " seconds ...")
            if proxyCnt != numProx:
                time.sleep(timeout)
        
        self.getUUID(endpoint)
        self.firewallUpdate(endpoint, endpoint1)
        self.getIP(endpoint, endpoint1, endpoint2)
    
    # Stop server
    def stop(self):
        endpoint = "/server"
        endpoint1 = "/stop"
        endpoint2 = "/storage"
        endpoint3 = "/private"
        self.getUUID(endpoint)
        self.getStorageUUID(endpoint2+endpoint3)
        self.destroy(endpoint, endpoint1, endpoint2)

    # Store IP Address
    def ip(self):
        endpoint = "/server"
        endpoint1 = "/firewall_rule"
        endpoint2 = "/ip_address"
        self.getUUID(endpoint)
        self.getIP(endpoint, endpoint1, endpoint2)

    # For degugging
    def uuid(self):
        endpoint = "/server"
        self.getUUID(endpoint)
        endpoint = "/storage/private"
        self.getStorageUUID(endpoint)
    
    # For degugging
    def firewall(self):
        endpoint = "/server"
        fendpoint = "/firewall_rule"
        self.getUUID(endpoint)
        self.firewallUpdate(endpoint, fendpoint)

    # For debugging
    def status(self):
        endpoint = "/server"
        self.getUUID(endpoint)
        self.getStatus(endpoint)
    

if __name__ == "__main__":
    LOGGER = LOGGING().loggingLog('Log File')
    INFO = LOGGING().infoLog('Info File')
    uuidFP = tempfile.TemporaryFile()
    storageFP = tempfile.TemporaryFile()

    
    parser = argparse.ArgumentParser()

    actionParser = parser.add_mutually_exclusive_group()
    actionParser.add_argument("--create", help = "Create Proxies", action = "store_true")
    actionParser.add_argument("--destroy", help = "Destroy All Servers. ", action = "store_true")
    actionParser.add_argument("--debug", help = "Debugging Mode ", action = "store_true")

    optionalParsel = parser.add_mutually_exclusive_group()
    optionalParsel.add_argument("-n", "--numProxies", type=int, nargs=1, help = "Number of proxies", default=1) #choices=range(1,51)
    optionalParsel.add_argument("-d", "--debugFunc", type=str, nargs=1, help = "Debug Functions", default="account")

    args = parser.parse_args()

    startTime = time.time()
    print("Running ...")

    if args.create:
        BACKUP = LOGGING().backupLog('Backup File')

        LOGGER.info("Create Mode!")
        if args.numProxies[0] <= 0 or args.numProxies[0] > 50:
            LOGGER.error("Number of proxies has to be between 1 and 50. Exiting ...")
            sys.exit(0)
        else:
            numProx = args.numProxies[0]
            LOGGER.info("Number of proxies chosen: " + str(numProx))
            ACCOUNT().create(numProx)
    
    elif args.destroy:
        LOGGER.info("Destroy Mode!")
        ACCOUNT().stop()

    elif args.debug:
        LOGGER.info("Debug Mode!")
        if args.debugFunc[0] == "account":
            LOGGER.info("Start Debug Account ...")
            ACCOUNT().check()
        elif args.debugFunc[0] == "uuid":
            LOGGER.info("Start Debug UUID ...")
            ACCOUNT().uuid()
        elif args.debugFunc[0] == "firewall":
            LOGGER.info("Start Debug Firewall ...")
            ACCOUNT().firewall()
        elif args.debugFunc[0] == "status":
            LOGGER.info("Start Debug Status ...")
            ACCOUNT().status()
        elif args.debugFunc[0] == "ip":
            LOGGER.info("Start Debug IP ...")
            ACCOUNT().ip()

    else:
        print("\nArguments required: [Action] [Optional]") 
        print("		Action: --create | --destroy | --debug") 
        print("		Optional: -n (number of proxies) | -d (debug function)")
        print("		          -n : 1 - 50              -d (account | uuid | firewall | status | ip)")
        print("		--help\n")

    uuidFP.close()
    storageFP.close()

    print("ProxyMaker successful. Run time: {}".format(time.time() - startTime))