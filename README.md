HTTP Proxy Creator (In Development)
===============================

Motivation
------------------------------------

To create multiple proxy servers using various cloud hosting providers (UpCloud, vultr) with the intention of purchasing limited edition apparels. I have been reselling these items to gain extra cash for college. Instead of purchasing proxies from other providers with triple or quadruple the cost of creating these proxies, I decided to learn the mechanics behind creating a proxy server and also automating the process by using APIs of the cloud hosting providers.


Guide
--------------------

Program is written in a sequential manner due to cloud providers have a "continuous creation of servers limit", once the limit is reached, the program with wait for 30 minutes before resuming. Logging is implemented to allow users to debug or check the current status of the running program. Once it is done, a text file is created with all the information of the proxies (Format: IP:PORT:USER:PASS).
The program is written with Python 3 and other modules.
Follow [this link](https://www.python.org/downloads/) to install Python 3.
Install modules:

        pip install requests json argparse

Running the program is easy. Only with a command line will create X amount of proxies servers.
Creating:

        python run.py --create -n 5

Destroying:

        python run.py --destroy
