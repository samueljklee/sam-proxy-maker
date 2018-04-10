import os, sys, time, string, random
import requests, base64, json
import logging
import tempfile
import argparse

LOGF    = "log.txt"
INFOF   = "info.txt"

class LOGGING:
    LogFile = LOGF
    InfoFile = INFOF

    def loggingLog(self,name):
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.FileHandler(self.LogFile,mode='w')
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        return logger
    
    def infoLog(self,name):
        formatter = logging.Formatter(fmt='%(message)s')
        handler = logging.FileHandler(self.InfoFile,mode='w')
        handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        return logger

class BASEAPI:
    credentials = "username:password"
    api = "https://api.upcloud.com/"
    api_v = "1.2"
    token = base64.b64encode(credentials.encode())
    USER = "fast"
    PASS = "slow"
    PORT = "3128"
    NUMSERVER = 0

    '''
    Get Account Information
    '''
    def getAccount(self, endpoint):
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

    '''
    Create Server
    '''
    def createServer(self, endpoint):
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json" 
        }
        data = {
            "server": {
                "zone": "us-chi1",
                "title": "Chicago Server ",
                "hostname": "server.samuel.com",
                "plan": "1xCPU-1GB",
                "user_data": "#!/bin/bash\nyum install squid wget httpd-tools -y\ntouch /etc/squid/passwd\nhtpasswd -b /etc/squid/passwd " + self.USER + " " + self.PASS + " \nwget -O /etc/squid/squid.conf https://raw.githubusercontent.com/samueljklee/ProxyMaker/master/squid1.conf --no-check-certificate \ntouch /etc/squid/blacklist.acl\nsystemctl restart squid.service\nsystemctl enable squid.service\niptables -I INPUT -p tcp --dport " + self.PORT + " -j ACCEPT\niptables-save",
                "storage_devices": {
                    "storage_device": [
                        {
                            "action": "clone",
                            "title": "CentOS Template",
                            "storage": "01000000-0000-4000-8000-000050010300",
                            "size": 10,
                            "tier": "maxiops"
                        }
                    ]
                },
                "login_user": {
                    "username": "root",
                }
            }
        }
        LOGGER.info("Creating Server ...")
        conn = requests.post(url, headers=headers, data=json.dumps(data))
        self.checkResponse(conn)

    ### Zone

    ### Plan

    ### Storage

    '''
    Get Server UUID
    '''
    def getUUID(self, endpoint):
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
            # Store UUID into temporary file
            uuidFP.write(bytes(server[i]["uuid"]+"\n", encoding="utf-8"))
            LOGGER.info("UUID: " + str(server[i]["uuid"]))
            
    
    '''
    Get Storage UUID
    '''
    def getStorageUUID(self, endpoint):
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
            storageFP.write(bytes(server[i]["uuid"]+"\n", encoding="utf-8"))
            LOGGER.info("UUID: " + str(server[i]["uuid"]))
            
    '''
    Update Firewall Rules
    '''
    def firewallUpdate(self, endpoint, fendpoint):
        # Wait for server to be created
        timeout = random.randint(0,3)
        LOGGER.info("Ready to update firewall in " + str(timeout) + " seconds.")
        time.sleep(timeout)

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
            data = {
                "firewall_rule": {
                    "action": "accept",
                    "comment": "Allow incoming traffic.",
                    "direction": "in",
                    "family": "IPv4",
                    "protocol": "tcp",
                    "destination_port_end": "3128",
                    "destination_port_start": "3128",

                }
            }
            conn = requests.post(url, headers=headers, data=json.dumps(data))
            self.checkResponse(conn)

            # Outgoing Traffic
            data = {
                "firewall_rule": {
                    "action": "accept",
                    "comment": "Allow outgoing traffic.",
                    "direction": "out",
                    "family": "IPv4",
                    "protocol": "tcp",
                    "source_port_end": "3128",
                    "source_port_start": "3128",

                }
            }

            conn = requests.post(url, headers=headers, data=json.dumps(data))
            self.checkResponse(conn)         

    '''
    Stop Server, Destroy Server, Destroy Storage
    '''
    def destroy(self, endpoint, endpoint1, endpoint2):
        uuidFP.seek(0)
        LOGGER.info("Stopping servers ...")
        for line in uuidFP:
            uuid = str(line,encoding="utf-8").strip("\n")
            url = self.api + self.api_v + endpoint + "/" + uuid + endpoint1
            headers = {
                "Authorization": "Basic " + self.token.decode(),
                "Content-Type": "application/json"
            }
            
            conn = requests.post(url, headers=headers)
            self.checkResponse(conn)
            
            timeout = random.randint(3,33)
            time.sleep(timeout)
            LOGGER.info("Stopping UUID: " + str(uuid) + ". Timeout stop for " + str(timeout) + " seconds.")    
        
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
                    LOGGER.info("UUID: " + str(uuid) + " not ready. Timeout for " + str(timeout) + " seconds.")
                    time.sleep(timeout)
                else:
                    timeout = random.randint(3,7)
                    LOGGER.info("Success destroyed UUID: " + str(uuid) + " . Starting next in " + str(timeout) + " seconds.")
                    time.sleep(timeout)

            LOGGER.info("Destroying UUID: " + str(uuid) + ".")  
        
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
                    timeout = random.randint(3,7)
                    LOGGER.info("Success destroyed storage UUID: " + str(uuid) + " . Starting next in " + str(timeout) + " seconds.")
                    time.sleep(timeout)

            LOGGER.info("Destroying Storage UUID: " + str(uuid) + ".")  

    '''
    Get IP address
    '''
    ### Check if it's not proxy server
    def getIP(self, endpoint):
        LOGGER.info("Finding IP Address ...")
        
        url = self.api + self.api_v + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        
        conn = requests.get(url, headers=headers)
        self.checkResponse(conn)
        res = conn.json()
        ipAddr = res["ip_addresses"]["ip_address"]
        for i in range(len(ipAddr)):
            if "public" in ipAddr[i].values() and "IPv4" in ipAddr[i].values():
                LOGGER.info("IP Adresss: " + ipAddr[i]["address"])
                INFO.info(ipAddr[i]["address"] + ":" + self.PORT + ":" + self.USER + ":" + self.PASS)

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
    '''
    def checkResponse(self, res):
        if str(res) == "<Response [204]>":
            LOGGER.info("Command Successful. No Content.")
            return True
        data = res.json()
        LOGGER.info(str(data))
        key = list(data.keys())
        if key[0] == 'error' :
            LOGGER.error("Error Code: " + data['error']['error_code'])
            if data['error']['error_code'] == "SERVER_STATE_ILLEGAL":
                return False
            elif data['error']['error_code'] == "UNAUTHORIZED_ADDRESS":
                return False
            else:
                return True
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

        while numProx > 0:
            LOGGER.info("Creating Proxy " + str(numProx) + " ...")
            self.createServer(endpoint)
            numProx -= 1
            if numProx % 3 == 0:
                # Wait between 1 minute ~ 7 minutes
                timeout = random.randint(60,420)
                LOGGER.info("Creating Server ... Timeout for " + str(timeout) + " ...")
                time.sleep(timeout)
        
        self.getUUID(endpoint)
        self.firewallUpdate(endpoint, endpoint1)
    
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
        endpoint = "/ip_address"
        self.getIP(endpoint)

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

    
    #ACCOUNT().check()
    #ACCOUNT().create()
    #ACCOUNT().uuid()
    #ACCOUNT().firewall()
    #ACCOUNT().stop()
    #ACCOUNT().status()

    if args.create:
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
        print("		          -n : 1 - 50              -d (account | uuid | firewall | status)")
        print("		--help\n")

    uuidFP.close()
    storageFP.close()