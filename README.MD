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
```yaml
domain: fatihsolen.com
dns_server: 127.0.0.1
```

### Configuration for vCenter Servers

Create vCenter configuration files in the "hypervisor_configs/vmware" directory. Each file should be named after the vCenter and have the following format:
```yaml
host: vcenter01.fatihsolen.local
username: vcenter_username
password: vcenter_password
```

### Configuration for Pure Storage Arrays

Create storage configuration files in the "storage_configs" directory. Each file should be named after the storage array and have the following format:
```yaml
pure_fa_api_url: purefa01.fatihsolen.local
pure_fa_api_token: **TOKEN**
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
python fscli.py dns get A example.com domain1
```

**Add DNS Record**
```sh
python fscli.py dns add A example.com 192.168.1.1 domain1 --ttl 3600
```

**Delete DNS Record**
```sh
python fscli.py dns del A example.com 192.168.1.1 domain1
```

**List DNS Records**
```sh
python fscli.py dns list domain1
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
