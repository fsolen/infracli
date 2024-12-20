# InfraCLI
https://fatihsolen.com
https://www.linkedin.com/in/fatihsolen/

InfraCLI is a unified command-line tool for managing Microsoft DNS Server records, VMware, Harvester, OpenNebula and Cloud Stack virtual machines (VMs) and PureStorage FLashArray// storage arrays. It provides functionalities to add, delete, list and modify DNS records, as well as to create, delete, list, snapshot and modify VMs and manage storage arrays for daily tasks. 

## Notes
* Added PHPIPAM integration for getting next available IP, Subnet, Route and DNS information.
* Openshift Virtualization (Kubevirt) (Harvester HCI works well but Openshift Virtualization not tested yet)
* OpenNebula supports added (Not fully tested)
* Apache Cloud Stack support added (Not fully tested)

## Planned
* Vault integration to secure authentication tokens

## Not Planned
* Proxmox support

##  Do not use in production yet! 

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

3. Run the CLI:
	```sh
	python fscli.py --help
	```

4. Shorten Command (Optional)
	```sh
	bash setup_fscli.sh
	```

## Configuration

### Configuration for Microsoft DNS Servers

Create DNS configuration files in the "dnsserver_configs" directory. Each file should be named after the domain and have the following format:
```yaml
domain: fatihsolen.com
dns_server: 127.0.0.1
```

### Configuration for vCenter Servers

Create vCenter configuration files in the "hypervisor_configs/vmware" directory. Each file should be named after the "vcenter" and have the following format:
```yaml
host: vcenter01.fatihsolen.local
username: vcenter_username
password: vcenter_password
```

### Configuration for Harvester HCI Clusters

Create vCenter configuration files in the "hypervisor_configs/harvester" directory. Each file should be named after the "harvester" and have the following format:
```yaml
harvester_api_url: https://harvester01.fatihsolen.local
harvester_api_token: **TOKEN**
```

### Configuration for OpenNebula Clusters

Create vCenter configuration files in the "hypervisor_configs/opennebula" directory. Each file should be named after the "one" and have the following format:
```yaml
opennebula_api_url: http://opennebula01.fatihsolen.local:2633/RPC2
opennebula_username: username
opennebula_password: password
```

### Configuration for Apache Cloud Stack Clusters

Create vCenter configuration files in the "hypervisor_configs/cloudstack" directory. Each file should be named after the "aos" and have the following format:
```yaml
  api_url: "https://cloudstack01.fatihsolen.local/client/api"
  api_key: "your_api_key"
  secret_key: "your_secret_key"
```

### Configuration for Pure Storage FlashArrays

Create storage configuration files in the "storage_configs" directory. Each file should be named after the storage array and have the following format:
```yaml
pure_fa_api_url: purefa01.fatihsolen.local
pure_fa_api_token: **TOKEN**
```

### Configuration for phpIPAM

Create storage configuration files in the "ipam_configs" directory. Each file should be named after the phpipam and have the following format:
```yaml
phpipam:
  base_url: "http://phpipam01.fatihsolen.local"
  app_id: "app_id"
  username: "username"
  password: "password"
```

### VM Host Group Profiles

Create VM profile files in the "vm_profiles" directory. Each file should be named after the profile and have the following format:
```yaml
# Example profile
name: web_server
cpu: 2
memory: 4096
disk: 40
network: default
```

## Usage Examples

### DNS Management

**Get DNS Record**
```sh
python fscli.py dns get <dns-record-type> <dns-record> <dns-server-name>
python fscli.py dns get A example.fatihsolen.com fatihsolen_com
python fscli.py dns get CNAME alias.fatihsolen.com fatihsolen_com
python fscli.py dns get PTR 123.123.123.123 fatihsolen_com
python fscli.py dns get TXT example.fatihsolen.com fatihsolen_com
python fscli.py dns get MX example.fatihsolen.com fatihsolen_com
```

**Add DNS Record** (PTR records are created automatically)
```sh
python fscli.py dns add <dns-record-type> <dns-record> <record-value> [ttl-value] [priority(only for MX records)] <dns-server-name>
python fscli.py dns add A example.fatihsolen.com 192.168.1.1 --ttl 3600 fatihsolen_com
python fscli.py dns add CNAME alias.fatihsolen.com example.fatihsolen.com --ttl 3600 fatihsolen_com
python fscli.py dns add TXT example.fatihsolen.com "v=spf1 include:fatihsolen.com ~all" --ttl 3600 fatihsolen_com
python fscli.py dns add MX example.fatihsolen.com mail.example.com --ttl 3600 --priority 10 fatihsolen_com
```

**Delete DNS Record**
```sh
python fscli.py dns del <dns-record-type> <dns-record> <record-value> <dns-server-name>
python fscli.py dns del A example.fatihsolen.com 192.168.1.1 fatihsolen_com
python fscli.py dns del CNAME alias.fatihsolen.com example.fatihsolen.com fatihsolen_com
python fscli.py dns del TXT example.fatihsolen.com "v=spf1 include:example.com ~all" fatihsolen_com
python fscli.py dns del MX example.fatihsolen.com mail.example.com fatihsolen_com
```

**List DNS Records**
```sh
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
python fscli.py hrv create <profile_name> <harvester_cluster_name>
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

#### OpenNebula
**Create VM**
```sh
python fscli.py one create <profile_name> <cluster_name>
```

**Delete VM**
```sh
python fscli.py one delete <vm_id> <cluster_name>
```

**List VMs**
```sh
python fscli.py one list <cluster_name>
```

**Modify VMs**
```sh
python fscli.py one modify <vm_id> <profile_name> <cluster_name>
```

#### Apache Cloud Stack
**Create VM**
```sh
python fscli.py aos create <profile_name> <cluster_name>
```

**Delete VM**
```sh
python fscli.py aos delete <vm_id> <cluster_name>
```

**List VMs**
```sh
python fscli.py aos list <cluster_name>
```

**Modify VMs**
```sh
python fscli.py aos modify <vm_id> <profile_name> <cluster_name>
```

### Pure FlashArray Management

**Create LUN**
```sh
python fscli.py storage create_lun <array_name> <volume_name> <size>
```

**Create Host**
```sh
python fscli.py storage create_host <array_name> <host_name> --iqn <iqn> --wwns <wwn1> <wwn2>
```

**Add Initiator to Host**
```sh
python fscli.py storage add_initiator <array_name> <host_name> <initiator_name> <initiator_type>
```

**Map Volume to Host**
```sh
python fscli.py storage map_volume <array_name> <volume-name> <host_name>
```

**Take Snapshot of LUN**
```sh
python fscli.py storage snapshot_lun <array_name> <volume-name> <snapshot-name>
```

**List All Hosts**
```sh
python fscli.py storage list_hosts <array_name>
```

**List All LUNs**
```sh
python fscli.py storage list_luns <array_name>
```

**List Host and LUN Mappings**
```sh
python fscli.py storage list_host_lun_mappings <array_name>
```
