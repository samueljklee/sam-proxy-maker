#!/bin/bash
yum install squid wget httpd-tools -y
touch /etc/squid/passwd
htpasswd -b /etc/squid/passwd hello world
wget -O /etc/squid/squid.conf https://raw.githubusercontent.com/samueljklee/ProxyMaker/master/data/setup.conf --no-check-certificate 
sed -i "s/3128/65002/g" /etc/squid/squid.conf 
touch /etc/squid/blacklist.acl
systemctl restart squid.service
systemctl enable squid.service
iptables -I INPUT -p tcp --dport 65002 -j ACCEPT
iptables-save
