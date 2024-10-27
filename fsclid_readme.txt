# dont forget to change psexec remote policy on dns servers // you can run Enable-PSRemoting -Force

fscli.py dns list example.com
 
fscli.py dns get A example.com domain1.com
 
fscli.py dns add A example.com 192.0.2.100 domain1.com --ttl 3600
fscli.py dns add MX example.com mail.example.com domain1.com --ttl 3600 --priority 10
fscli.py dns add TXT example.com "This is a test TXT record" domain1.com --ttl 3600
fscli.py dns add CNAME www.example.com example.com domain1.com --ttl 3600
 
fscli.py dns del A example.com 192.0.2.100 domain1.com
fscli.py dns del MX mail.example.com mail.example.com domain1.com --priority 10
fscli.py dns del TXT example.com "This is a test TXT record" domain1.com
fscli.py dns del CNAME www.example.com example.com domain1.com


./fscli.py dns [get|add|del|list] <args>
./fscli.py vm [create|delete|list|snapshot|modify] <args>
