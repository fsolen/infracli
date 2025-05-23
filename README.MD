# InfraCLI
https://fatihsolen.com
https://www.linkedin.com/in/fatihsolen/

InfraCLI is a unified command-line tool for managing Microsoft DNS Server records, VMware, Harvester and Cloud Stack virtual machines (VMs) and PureStorage FLashArray// storage arrays. It provides functionalities to add, delete, list and modify DNS records, as well as to create, delete, list, snapshot and modify VMs and manage storage arrays for daily tasks. 

## Notes
* Added PHPIPAM integration for getting next available IP, Subnet, Route and DNS information. ** Roadmap : "I'll change phpIPAM with Netbox"
* Openshift Virtualization (Kubevirt) (Harvester HCI works well but Openshift Virtualization not tested yet)
* Apache Cloud Stack support added (Not fully tested)
* OpenBAO integration done but needs optimization.

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

4. Shorten Commands (Optional)
	for Linux Distros 
	```sh
	bash setup_linux_fscli.sh
	```
	for Windows OS
	```sh
	.\setup_win_fscli.bat
	```

## Configuration

The configuration for sites and services is stored in `configs/sites.yaml`. Each site can have multiple hypervisors, storage systems and DNS servers.

```yaml
sites:
  istanbul:
    hypervisors:
      - type: vmware
        host: ivcenter01.fatihsolen.local
        vault_path: "secret/istanbul/vmware/ivcenter01"
      - type: vmware
        host: ivcenter02.fatihsolen.local
        vault_path: "secret/istanbul/vmware/ivcenter02"
      - type: harvester # KubeVirt
        host: iharvester01.fatihsolen.local
        api_url: "https://iharvester01.fatihsolen.local"
        vault_path: "secret/istanbul/harvester/iharvester01"
      - type: harvester # KubeVirt
        host: iharvester02.fatihsolen.local
        api_url: "https://iharvester02.fatihsolen.local"
        vault_path: "secret/istanbul/harvester/iharvester02"
      - type: cloudstack
        host: icloudstack01.fatihsolen.local/client/api
        api_url: "https://icloudstack01.fatihsolen.local/client/api"
        vault_path: "secret/istanbul/cloudstack/icloudstack01"
      - type: cloudstack
        host: icloudstack02.fatihsolen.local/client/api
        api_url: "https://icloudstack02.fatihsolen.local/client/api"
        vault_path: "secret/istanbul/cloudstack/icloudstack02"
    storage:
      - type: purefa
        host: ipurefa01.fatihsolen.local
        api_url: "https://ipurefa01.fatihsolen.local"
        vault_path: "secret/istanbul/purefa/ipurefa01"
      - type: purefa
        host: ipurefa02.fatihsolen.local
        api_url: "https://ipurefa02.fatihsolen.local"
        vault_path: "secret/istanbul/purefa/ipurefa02"
    dns:
      - type: msdns
        host: msdns.fatihsolen.local
        vault_path: "secret/istanbul/msdns"
    ipam:
      - type: phpipam
        host: iipam.fatihsolen.local
        base_url: "https://iipam.fatihsolen.local"
        vault_path: "secret/istanbul/phpipam"
    vault:
      - type: openboa
        host: vault.fatihsolen.local
  ankara:
    hypervisors:
      - type: vmware
        host: avcenter01.fatihsolen.local
        vault_path: "secret/ankara/vmware/avcenter01"
      - type: vmware
        host: avcenter02.fatihsolen.local
        vault_path: "secret/ankara/vmware/avcenter02"
      - type: harvester # KubeVirt
        host: aharvester01.fatihsolen.local
        api_url: "https://aharvester01.fatihsolen.local"
        vault_path: "secret/ankara/harvester/aharvester01"
      - type: harvester # KubeVirt
        host: aharvester02.fatihsolen.local
        api_url: "https://aharvester02.fatihsolen.local"
        vault_path: "secret/ankara/harvester/aharvester02"
      - type: cloudstack
        host: acloudstack01.fatihsolen.local/client/api
        api_url: "https://acloudstack01.fatihsolen.local/client/api"
        vault_path: "secret/ankara/cloudstack/acloudstack01"
      - type: cloudstack
        host: acloudstack02.fatihsolen.local/client/api
        api_url: "https://acloudstack02.fatihsolen.local/client/api"
        vault_path: "secret/ankara/cloudstack/acloudstack02"
    storage:
      - type: purefa
        host: apurefa01.fatihsolen.local
        api_url: "https://apurefa01.fatihsolen.local"
        vault_path: "secret/ankara/purefa/apurefa01"
      - type: purefa
        host: apurefa02.fatihsolen.local
        api_url: "https://apurefa02.fatihsolen.local"
        vault_path: "secret/ankara/purefa/apurefa02"
    dns:
      - type: msdns
        host: msdns.fatihsolen.local
        vault_path: "secret/ankara/msdns"
    ipam:
      - type: phpipam
        host: aipam.fatihsolen.local
        base_url: "https://aipam.fatihsolen.local"
        vault_path: "secret/ankara/phpipam"
    vault:
      - type: openboa
        host: vault.fatihsolen.local
```

### VM Host Group Profiles

Create VM profile files in the `vm_profiles` directory. Each file should be named after the profile and have the following format:
```yaml
# Example profile manifest
hostname_pattern: ipa-{index}
template_name: opensuse-leap-15-v1
networks:
  - name: "net1"
    vlan: "vlan101"
  - name: "net2"
    vlan: "vlan102"
cpu: 4
memory: 8192
disks:
  - name: "disk1"
    size_gb: 50
  - name: "disk2"
    size_gb: 100
```

## Usage Examples

### DNS Management

**Get DNS Record**
```sh
python fscli.py dns get <site> <server> <dns-record-type> <dns-record> <dns-server-name>
python fscli.py dns get istanbul msdns A example.fatihsolen.com fatihsolen_com
python fscli.py dns get istanbul msdns alias.fatihsolen.com fatihsolen_com
python fscli.py dns get istanbul msdns PTR 123.123.123.123 fatihsolen_com
python fscli.py dns get istanbul msdns TXT example.fatihsolen.com fatihsolen_com
python fscli.py dns get ankara msdns MX example.fatihsolen.com fatihsolen_com
```

**Add DNS Record** (PTR records are created automatically)
```sh
python fscli.py dns add <site> <dns_name> <dns-record-type> <dns-record> <record-value> [ttl-value] [priority(only for MX records)] <dns-server-name>
python fscli.py dns add istanbul msdns A example.fatihsolen.com 192.168.1.1 --ttl 3600 fatihsolen_com
python fscli.py dns add istanbul msdns CNAME alias.fatihsolen.com example.fatihsolen.com --ttl 3600 fatihsolen_com
python fscli.py dns add istanbul msdns TXT example.fatihsolen.com "v=spf1 include:fatihsolen.com ~all" --ttl 3600 fatihsolen_com
python fscli.py dns add istanbul msdns MX example.fatihsolen.com mail.example.com --ttl 3600 --priority 10 fatihsolen_com
```

**Delete DNS Record**
```sh
python fscli.py dns del <site> <dns_name> <dns-record-type> <dns-record> <record-value> <dns-server-name>
python fscli.py dns del istanbul msdns A example.fatihsolen.com 192.168.1.1 fatihsolen_com
python fscli.py dns del istanbul msdns CNAME alias.fatihsolen.com example.fatihsolen.com fatihsolen_com
python fscli.py dns del istanbul msdns TXT example.fatihsolen.com "v=spf1 include:example.com ~all" fatihsolen_com
python fscli.py dns del istanbul msdns MX example.fatihsolen.com mail.example.com fatihsolen_com
```

**List DNS Records**
```sh
python fscli.py dns list <site> <dns_name> <dns-server-name>
python fscli.py dns list istanbul msdns fatihsolen.com
```

### VM Management

#### For all hypervisors

**Create VM**
```sh
python fscli.py vm create <profile_name> <site> <hypervisor_name>
```

**Delete VM**
```sh
python fscli.py vm delete <vm_name> <site> <hypervisor_name>
```

**List VMs**
```sh
python fscli.py vm list <site> <hypervisor_name>
```

**Create VM Snapshot**
```sh
python fscli.py vm snapshot <vm_name> <site> <hypervisor_name>
```

**Modify VM**
```sh
python fscli.py vm modify <vm_name> <profile_name> <site> <hypervisor_name>
```

### Pure FlashArray Management

**Create LUN**
```sh
python fscli.py storage create_lun <site> <array_name> <volume_name> <size>
```

**Create Host**
```sh
python fscli.py storage create_host <site> <array_name> <host_name> --iqn <iqn> --wwns <wwn1> <wwn2>
```

**Add Initiator to Host**
```sh
python fscli.py storage add_initiator <site> <array_name> <host_name> <initiator_name> <initiator_type>
```

**Map Volume to Host**
```sh
python fscli.py storage map_volume <site> <array_name> <volume-name> <host_name>
```

**Take Snapshot of LUN**
```sh
python fscli.py storage snapshot_lun <site> <array_name> <volume-name> <snapshot-name>
```

**List All Hosts**
```sh
python fscli.py storage list_hosts <site> <array_name>
```

**List All LUNs**
```sh
python fscli.py storage list_luns <site> <array_name>
```

**List Host and LUN Mappings**
```sh
python fscli.py storage list_host_lun_mappings <site> <array_name>
```
