# InfraCLI
https://fatihsolen.com
https://www.linkedin.com/in/fatihsolen/
InfraCLI is a unified command-line tool for managing Microsoft DNS Server records, VMware and Harvester virtual machines (VMs) and PureStorage FLashArray// storage arrays. It provides functionalities to add, delete, list and modify DNS records, as well as to create, delete, list, snapshot and modify VMs and manage storage arrays for daily tasks. 
Openshift Virtualization (Kubevirt) -plus may be OpenNebula- supports under dev. 
Vault integration for authentication tokens under dev.
#  Do not use in production yet! 
## Installation
1. Clone the repository:
	```sh
	git clone https://github.com/fsolen/infracli.git
	cd infracli
	```
2. Install the required dependencies:
	```sh
	pip install -r requirements.txt
	```
## Configuration

### Configuration for Microsoft DNS Servers

Create DNS configuration files in the "dnsserver_configs" directory. Each file should be named after the domain and have the following format:
Create DNS configuration files in the "dnsserver_configs" directory. Each file should be named after the domain and have the following format (For this example, the file name should be fatihsolen_com.yaml):
```yaml
domain: fatihsolen.com
dns_server: 127.0.0.1
dns_server: 123.123.123.123
username: admin
password: secret
```
### Configuration for vCenter Servers
@@ -74,22 +76,36 @@ network: default
**Get DNS Record**
```sh
python fscli.py dns get A example.com domain1
python fscli.py dns get <dns-record-type> <dns-record> <dns-server-name>
python fscli.py dns get A example.fatihsolen.com fatihsolen_com
python fscli.py dns get CNAME alias.fatihsolen.com fatihsolen_com
python fscli.py dns get PTR 123.123.123.123 fatihsolen_com
python fscli.py dns get TXT example.fatihsolen.com fatihsolen_com
python fscli.py dns get MX example.fatihsolen.com fatihsolen_com
```

**Add DNS Record**
```sh
python fscli.py dns add A example.com 192.168.1.1 domain1 --ttl 3600
python fscli.py dns add <dns-record-type> <dns-record> <record-value> [ttl-value] [priority(only for MX records)] <dns-server-name>
python fscli.py dns add A example.fatihsolen.com 192.168.1.1 --ttl 3600 fatihsolen_com
python fscli.py dns add CNAME alias.fatihsolen.com example.fatihsolen.com --ttl 3600 fatihsolen_com
python fscli.py dns add TXT example.fatihsolen.com "v=spf1 include:fatihsolen.com ~all" --ttl 3600 fatihsolen_com
python fscli.py dns add MX example.fatihsolen.com mail.example.com --ttl 3600 --priority 10 fatihsolen_com
```

**Delete DNS Record**
```sh
python fscli.py dns del A example.com 192.168.1.1 domain1
python fscli.py dns del <dns-record-type> <dns-record> <record-value> <dns-server-name>
python fscli.py dns del A example.fatihsolen.com 192.168.1.1 fatihsolen_com
python fscli.py dns del CNAME alias.fatihsolen.com example.fatihsolen.com fatihsolen_com
python fscli.py dns del TXT example.fatihsolen.com "v=spf1 include:example.com ~all" fatihsolen_com
python fscli.py dns del MX example.fatihsolen.com mail.example.com fatihsolen_com
```

**List DNS Records**
```sh
python fscli.py dns list domain1
python fscli.py dns list <dns-server-name>
python fscli.py dns list fatihsolen_com
```

### VM Management
#### VMware vSphere
**Create VM**
```sh
python fscli.py vm create <profile_name> <vcenter_name>
```
**Delete VM**
```sh
python fscli.py vm delete <vm_name> <vcenter_name>
```
**List VMs**
```sh
python fscli.py vm list <vcenter_name>
```
**Create VM Snapshot**
```sh
python fscli.py vm snapshot <vm_name> <vcenter_name>
```
**Modify VM**
```sh
python fscli.py vm modify <vm_name> <profile_name> <vcenter_name>
```
#### Harvester HCI
**Create VM**
```sh
python fscli.py hrv create <vm_name> <harvester_cluster_name>
```
**Delete VM**
```sh
python fscli.py hrv delete <vm_name> <harvester_cluster_name>
```
**List VMs**
```sh
python fscli.py hrv list <harvester_cluster_name>
```
**Modify VMs**
```sh
python fscli.py hrv modify <vm_name> <profile_name> <harvester_cluster_name>
```
### Storage Management
**Create LUN**
```sh
python fscli.py storage create_lun <purestorage_name> <volume-name> 100G
```
**Create Host**
```sh
python fscli.py storage create_host <purestorage_name> <host_name>
```
**Map Volume to Host**
```sh
python fscli.py storage map_volume <purestorage_name> <volume-name> <host_name>
```
**Take Snapshot of LUN**
```sh
python fscli.py storage snapshot_lun <purestorage_name> <volume-name> <snapshot-name>
```
**List Hosts**
```sh
python fscli.py storage list_hosts <purestorage_name>
```
**List LUNs**
```sh
python fscli.py storage list_luns <purestorage_name>
```
