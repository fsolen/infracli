Example commands, i will merge that to main cli later.

fsclid.py dns list example.com
 
fsclid.py dns get A example.com domain1.com
 
fsclid.py dns add A example.com 192.0.2.100 domain1.com --ttl 3600
fsclid.py dns add MX example.com mail.example.com domain1.com --ttl 3600 --priority 10
fsclid.py dns add TXT example.com "This is a test TXT record" domain1.com --ttl 3600
fsclid.py dns add CNAME www.example.com example.com domain1.com --ttl 3600
 
fsclid.py dns del A example.com 192.0.2.100 domain1.com
fsclid.py dns del MX mail.example.com mail.example.com domain1.com --priority 10
fsclid.py dns del TXT example.com "This is a test TXT record" domain1.com
fsclid.py dns del CNAME www.example.com example.com domain1.com
