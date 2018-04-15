import os, sys, time, string, random
import requests
import logging
import threading
import argparse

DEBUG	= True
TOKEN	= "Token"
INFO 	= "info.txt"
LOGS 	= "log.txt"
PORT	= "8080"

"""
class thread(threading.Thread):
	def __init__(self,threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		if DEBUG: print("Starting Thread " + str(self.threadID))
		LOGGER.info("Starting Thread " + str(self.threadID))
		connect(self.threadID)
		LOGGER.info("Exiting Thread " + str(self.threadID))
		if DEBUG: print("Exiting Thread " + str(self.threadID))
"""
def loggerFormat(name):
	formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	handler = logging.FileHandler(LOGS,mode='w')
	handler.setFormatter(formatter)
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(handler)
	return logger

# To store IP:PORT:USER:PASS after creation
def infoLog(name):
	formatter = logging.Formatter(fmt='%(message)s')
	handler = logging.FileHandler(INFO,mode='w')
	handler.setFormatter(formatter)
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(handler)
	return logger

def connect(threadNum):
	setup()
	dcid, osiid, vpsplanid, scriptID, username, password = getInfo(threadNum)
	subid = createVm(threadNum, dcid, osiid, vpsplanid, scriptID)
	ip = extractIP(threadNum, subid)
	info = ip + ":" + PORT +":" + username + ":" + password
	log = str(time.ctime(time.time())) + ": " + "Thread " + str(threadNum) + " created proxy: " + ip + ":" + PORT +":" + username + ":" + password
	if DEBUG: print(info)
	INFOER.info(info)
	LOGGER.info(str(threadNum) + " " + log)

def headers():
	return {'API-Key': TOKEN,}

def setup():
	# Vultr Token
	if DEBUG: print("TOKEN: ", TOKEN)
	LOGGER.info("Token: " + TOKEN)
	LOGGER.info("Connecting ...")
	print("Connecting ...")

	# get Account Information
	req =  requests.get('https://api.vultr.com/v1/account/info', headers = headers())
	if DEBUG: print(req)
	LOGGER.info("Account Info Response Code: " + str(req))
	checkResponse(0, req,"Account")
	response = req.json() 
	if DEBUG: print("Response (dict): ",response)

	print("Connected!")
	LOGGER.info("Connected!")
	
def getInfo(threadNum):
	# get DCID, OSIID, VPSPLANID
	dcid = getDcid(threadNum)
	osiid = getOsiid(threadNum)
	vpsplanid = getVpsplanid(threadNum)

	# ScriptID, Username, Password
	scriptID, username, password = createScriptId(threadNum)
	if DEBUG: print("DCID {} OSIID {} VPSPLANID {} SCRIPTID {}".format(dcid,osiid,vpsplanid,scriptID))
	LOGGER.info(("T{}: DCID {} OSIID {} VPSPLANID {} SCRIPTID {}".format(threadNum, dcid,osiid,vpsplanid,scriptID)))
	return dcid, osiid, vpsplanid, scriptID, username, password


# DCID integer Location in which to create the server.
def getDcid(threadNum):
	### By default choose 2 :  Chicago
	req = requests.get('https://api.vultr.com/v1/regions/list')
	LOGGER.info("DCID Response Code: " + str(req))
	checkResponse(threadNum, req,"DCID")
	response = req.json()
	if DEBUG: print(response['2'])
	### Hardcoded
	return 2

# OSID integer Operating system to use.
def getOsiid(threadNum):
	### By default choose 167 for CentOS
	req = requests.get('https://api.vultr.com/v1/os/list')
	LOGGER.info("OSID Response Code: " + str(req))
	checkResponse(threadNum, req,"OSIID")
	response = req.json()
	if DEBUG: print(response['167'])
	### Hardcoded
	return 167

# VPSPLANID integer Plan to use when creating this virtual machine.
# Only check for VC2
def getVpsplanid(threadNum):
	### Accept other DCID
	"""
	req = requests.get('https://api.vultr.com/v1/regions/availability_vdc2?DCID=2')
	LOGGER.info(str(threadNum) + " VPSPLANID VDC2 Response Code: " + str(req))
	checkResponse(threadNum, req,"VPSPLANID VDC2")
	response = req.json()
	LOGGER.info(str(threadNum) + " Return: " + str(response))
	print("Available: "+str(response))

	if response == []:
		print("No server available. Trying VC2 ...")
		LOGGER.warning("No server available. Trying VC2 ...")
	"""
	reqVC2 = requests.get('https://api.vultr.com/v1/regions/availability?DCID=1')
	LOGGER.info(str(threadNum) + " VPSPLANID VC2 Response Code: " + str(reqVC2))
	checkResponse(threadNum, reqVC2,"VPSPLANID VC2")
	response = reqVC2.json()
	LOGGER.info(str(threadNum) + " Return: " + str(response))
	print("Available: "+str(response))
	if response == []:
		LOGGER.warning("No server available. Exiting ...")
		print("No server available. Exiting ...")
		sys.exit(0)

	if DEBUG: print(response[0])
	return response[0]

def createScriptId(threadNum):
	username, password = createUserPass()
	data = [
  		('name', 'startup'),
  		('script',"#!/bin/bash\nyum install squid wget httpd-tools -y\ntouch /etc/squid/passwd\nhtpasswd -b /etc/squid/passwd " + username + " " + password + " \nwget -O /etc/squid/squid.conf https://raw.githubusercontent.com/dzt/easy-proxy/master/confg/userpass/squid.conf --no-check-certificate \ntouch /etc/squid/blacklist.acl\nsystemctl restart squid.service\nsystemctl enable squid.service\niptables -I INPUT -p tcp --dport 3128 -j ACCEPT\niptables-save" ),
	]
	req = requests.post('https://api.vultr.com/v1/startupscript/create', headers=headers(), data=data)
	LOGGER.info(str(threadNum) + " SCRIPTID Response Code: " + str(req))
	LOGGER.info(str(threadNum) + " Username: " + username + " Password: " + password)
	checkResponse(threadNum, req,"ScriptID")
	response = req.json()
	if DEBUG: print(response)
	return response['SCRIPTID'], username, password

def createVm(threadNum, dcid, osiid, vpsplanid, scriptID):
	print("Creating Virtual Machine ...")
	LOGGER.info(str(threadNum) + " Creating Virtual Machine ...")
	data = [
		('DCID',dcid),
  		('VPSPLANID', vpsplanid),
  		('OSID', osiid),
		('SCRIPTID', scriptID),
	]
	req = requests.post('https://api.vultr.com/v1/server/create', headers=headers(), data=data)
	LOGGER.info(str(threadNum) + " SUBID Response Code: " + str(req))

	# Vultr Rate Limit 2 server per seconds
	while str(req) == "<Response [503]>":
		timeOut = random.randint(3,10) 
		print("Error 503. Timeout for "+ str(timeOut) +" seconds.")
		time.sleep(timeOut)
		req = requests.post('https://api.vultr.com/v1/server/create', headers=headers(), data=data)

	checkResponse(threadNum, req,"CreateServer")
	response = req.json()

	if DEBUG: print(response)

	timeout = random.randint(30,90)
	print("Setting up Virtual Machine. Waiting for "+ str(timeout) + " seconds.")
	LOGGER.info(str(threadNum) + " Setting up Virtual Machine. Waiting for "+ str(timeout) + " seconds.")
	time.sleep(timeout)

	return response['SUBID']

def extractIP(threadNum, subid):
	# list IPv4 information of a virtual machine 
	req = requests.get("https://api.vultr.com/v1/server/list_ipv4?SUBID="+subid, headers=headers())
	LOGGER.info(str(threadNum) + " IP Info Response Code: " + str(req))
	checkResponse(threadNum, req,"IPv4 Info")
	response = req.json()
	ip = response[subid][0]['ip']

	# Check if virtual machine is not ready.
	while ip == "0.0.0.0":
		timeout = random.randint(30,60)
		print("Waiting for Virtual Machine to be ready. Waiting for "+ str(timeout) + " seconds.")
		LOGGER.info(str(threadNum) + " Waiting for Virtual Machine to be ready. Waiting for "+ str(timeout) + " seconds.")
		time.sleep(timeout)

		req = requests.get("https://api.vultr.com/v1/server/list_ipv4?SUBID="+subid, headers=headers)
		response = req.json()
		ip = response[subid][0]['ip']
	
	if DEBUG: print("Successfully connected to IP: ", ip)
	LOGGER.info(str(threadNum) + " Successfully connected to IP: "+ ip)
	
	return ip

# Destroy Server
def destroy(subid):
	data = [
		('SUBID',subid),
	]
	req = requests.post('https://api.vultr.com/v1/server/destroy', headers=headers(), data=data)
	LOGGER.info("DESTROY Response Code: " + str(req))
	checkResponse(0, req,"Destroy")
	response = req.json()

	if DEBUG: print("Destroy: ", response)	
	
	return response

# Destroy All Servers
def destroyAll(infoFile):
	req = requests.get('https://api.vultr.com/v1/server/list', headers=headers())
	LOGGER.info("DESTROY ALL Response Code: " + str(req))
	checkResponse(0, req,"Destroy All")
	response = req.json()

	### ERROR 412 NEED TO WAIT FOR 5 MINS TO DESTROY A SERVER

	# Destroy Server
	if response != []:
		for key,_ in response.items():
			data = [
				('SUBID',key)
			]
			req = requests.post('https://api.vultr.com/v1/server/destroy', headers=headers(), data=data)
			checkResponse(0, req,"Destroy SUBID: " + key)
			LOGGER.info("Desctroying SUBID: " + key)
			### CHANGE TIME.SLEEP, IT'S TAKING TOO LONG
			time.sleep(3)
	else:
		print("No active servers. Skipping Destroy Servers.")
		LOGGER.warning("No active servers. Skipping Destroy Servers.")

	# Destroy Scripts
	req = requests.get("https://api.vultr.com/v1/startupscript/list",headers=headers())
	response = req.json()
	if response != []:
		for key,_ in response.items():
			data = [
				('SCRIPTID',key)
			]
			req = requests.post("https://api.vultr.com/v1/startupscript/destroy",headers=headers(),data=data)
			checkResponse(0, req,"Destroy Script: " + str(key))
			LOGGER.info("Destroying SCRIPTID: " + key)
			### CHANGE TIME.SLEEP, IT'S TAKING TOO LONG
			time.sleep(3)
	else:
		print("No active scripts. Skipping Destroy Scripts.")
		LOGGER.warning("No active scripts. Skipping Destroy Scripts.")

	if os.path.exists(infoFile):
		print("Removing " + infoFile)
		os.remove(INFO)

	print("Destroyed All Servers")

# Destroy all scripts
def destoryScripts():
	# Destroy Scripts
	req = requests.get("https://api.vultr.com/v1/startupscript/list",headers=headers())
	response = req.json()
	if response != []:
		for key,_ in response.items():
			data = [
				('SCRIPTID',key)
			]
			req = requests.post("https://api.vultr.com/v1/startupscript/destroy",headers=headers(),data=data)
			checkResponse(0, req,"Destroy Script: " + str(key))
			LOGGER.info("Destroying SCRIPTID: " + key)
			### CHANGE TIME.SLEEP, IT'S TAKING TOO LONG
			time.sleep(1)
	else:
		print("No active scripts. Skipping Destroy Scripts.")
		LOGGER.warning("No active scripts. Skipping Destroy Scripts.")	

# Create random Username and Password
def createUserPass():
	username = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
	password = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
	return username, password

def checkResponse(threadNum, response,var):
	if str(response) == "<Response [200]>":
		if DEBUG: print(var + " Connected/Created/Found/Destroyed")
		if var == "Account":
			if DEBUG: print(var + " Connected")
			LOGGER.info(str(threadNum) + " " + var + " Connected")
		elif var == "DCID" or var == "OSIID" or var == "VPSPLANID VDC2" or var == "ScriptID" or var == "CreateServer" or var == "IPv4 Info":
			if DEBUG: print(var + " Found")
			LOGGER.info(str(threadNum) + " " + var + " Found")
		elif "Destroy" in var:
			if DEBUG: print(var + " Destroyed")
			LOGGER.info(str(threadNum) + " " + var + " Destroyed")

	else:
		print("Fail to connect to Token. Error: " + var)
		print("Error response: "+ str(response))
		LOGGER.error("Fail to connect to Token. Error: " + var)
		LOGGER.error("Error response: "+ str(response))
		sys.exit(0)

if __name__ == "__main__":
	LOGGER = loggerFormat('vultr')
	INFOER = infoLog('info')
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--create", help = "Create Proxies", action = "store_true")
	parser.add_argument("--destroyAll", help = "Destroy All Servers. NOTE: " + INFO + " will be deleted.", action = "store_true")
	parser.add_argument("--destroyScripts", help = "Destroy All Scripts. ", action = "store_true")

	optionalParsel = parser.add_mutually_exclusive_group()
	optionalParsel.add_argument("-n", "--numProxies", type=int, nargs=1, help = "Number of proxies", default=1) #choices=range(1,51)
	optionalParsel.add_argument("-d", "--debugFunc", type=str, nargs=1, help = "Debug Functions", default="account")

	args = parser.parse_args()

	print("Starting ...")
	LOGGER.info("Starting ...")

	if args.create:
		print("Creating ...")
		if args.numProxies[0] <= 0:
			if DEBUG: print("Number of Proxies has to be a postive number.")
			if DEBUG: print("Exiting ...")
			LOGGER.error("Number of Proxies has to be a postive number. Exiting ...")
			sys.exit(0)

		argsProxy = args.numProxies[0]

		while argsProxy > 0:
			
			print("Creating Proxy " + str(argsProxy % 100))
			if argsProxy % 3 == 0:
				timeout = random.randint(60,300)
			elif argsProxy % 7 == 0:
				timeout = random.randint(300,900)
			else:
				timeout = random.randint(3,7)

			connect(argsProxy%100)
			LOGGER.info("Creating " + str(argsProxy % 100) + " proxy. Timeout for " + str(timeout) + " seconds.")
			time.sleep(timeout)	

			argsProxy -= 1

	elif args.destroyAll:
		print("Destroying ...")
		LOGGER.info("Destroying ...")
		setup()
		destroyAll(INFO)
	
	elif args.destroyScripts:
		setup()
		destoryScripts()
	else:
		print("\nArguments required: :") 
		print("		--create [Number of proxies]") 
		print("		--destroyAll")
		print("		--help\n")

	print("Exiting ...")
		