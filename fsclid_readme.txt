Example commands, i will merge that to main cli later.

fsclid.py list example.com

fsclid.py get A example.com domain1.com

fsclid.py add A example.com 192.0.2.100 domain1.com --ttl 3600
fsclid.py add MX example.com mail.example.com domain1.com --ttl 3600 --priority 10
fsclid.py add TXT example.com "This is a test TXT record" domain1.com --ttl 3600
fsclid.py add CNAME www.example.com example.com domain1.com --ttl 3600

fsclid.py del A example.com 192.0.2.100 domain1.com
fsclid.py del MX example.com mail.example.com domain1.com --priority 10
fsclid.py del TXT example.com "This is a test TXT record" domain1.com
fsclid.py del CNAME www.example.com example.com domain1.com
