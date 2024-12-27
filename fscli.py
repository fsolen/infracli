import argparse
import os
import yaml
import logging
from tabulate import tabulate
from managers.msdns_manager import DNSManager
from managers.vmware_manager import VMManager
from managers.purestorage_manager import StorageManager
from managers.harvester_manager import HarvesterManager
from managers.cloudstack_manager import CloudStackManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_profile(profile_name):
    profile_path = os.path.join("vm_profiles", f"{profile_name}.yaml")
    if not os.path.exists(profile_path):
        logger.error(f"Profile {profile_name} not found at {profile_path}")
        return None
    with open(profile_path, 'r') as f:
        return yaml.safe_load(f)

def load_config():
    config_path = os.path.join("configs", "sites.yaml")
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at {config_path}")
        return None
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_manager(site, service_type, host_name):
    config = load_config()
    if not config:
        return None
    site_config = config['sites'][site]
    service_config = next((s for s in site_config[service_type] if s['host'] == host_name), None)
    if not service_config:
        logger.error(f"{service_type.capitalize()} service with host '{host_name}' not found in site '{site}'")
        return None
    
    if service_type == 'hypervisors':
        if service_config['type'] == 'vmware':
            return VMManager(site_config, "vm_profiles")
        elif service_config['type'] == 'harvester':
            return HarvesterManager(site_config, "vm_profiles")
        elif service_config['type'] == 'cloudstack':
            return CloudStackManager(site_config, "vm_profiles")
    elif service_type == 'storage':
        return StorageManager(site_config)
    elif service_type == 'dns':
        return DNSManager(site_config)
    return None

def main():
    parser = argparse.ArgumentParser(description='Unified DNS, VM, and Storage Management Tool')
    subparsers = parser.add_subparsers(dest='tool', required=True)

    # DNS Management Parser
    dns_parser = subparsers.add_parser('dns', help='DNS management commands')
    dns_subparsers = dns_parser.add_subparsers(dest='command', required=True)

    # DNS Get Command
    get_parser = dns_subparsers.add_parser('get', help='Get DNS record')
    get_parser.add_argument('site', help='Name of the site')
    get_parser.add_argument('dns_name', help='Name of the DNS server')
    get_parser.add_argument('record_type', choices=['A', 'CNAME', 'PTR', 'TXT', 'MX'], help='Type of DNS record')
    get_parser.add_argument('name', help='Name of the DNS record')
    get_parser.add_argument('domain', help='Domain name to get DNS server address')

    # DNS Add Command
    add_parser = dns_subparsers.add_parser('add', help='Add DNS record')
    add_parser.add_argument('site', help='Name of the site')
    add_parser.add_argument('dns_name', help='Name of the DNS server')
    add_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    add_parser.add_argument('name', help='Name of the DNS record')
    add_parser.add_argument('value', help='Value of the DNS record')
    add_parser.add_argument('--ttl', type=int, default=3600, help='Time to live of the DNS record')
    add_parser.add_argument('domain', help='Domain name to get DNS server address')
    add_parser.add_argument('--priority', type=int, help='Priority for MX record')

    # DNS Delete Command
    del_parser = dns_subparsers.add_parser('del', help='Delete DNS record')
    del_parser.add_argument('site', help='Name of the site')
    del_parser.add_argument('dns_name', help='Name of the DNS server')
    del_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    del_parser.add_argument('name', help='Name of the DNS record')
    del_parser.add_argument('value', help='Value of the DNS record')
    del_parser.add_argument('domain', help='Domain name to get DNS server address')

    # DNS List Command
    list_parser = dns_subparsers.add_parser('list', help='List all DNS records')
    list_parser.add_argument('site', help='Name of the site')
    list_parser.add_argument('dns_name', help='Name of the DNS server')
    list_parser.add_argument('domain', help='Domain name to get DNS server address')

    # VM Management Parser
    vm_parser = subparsers.add_parser('vm', help='VM management commands')
    vm_subparsers = vm_parser.add_subparsers(dest='command', required=True)

    # VM Create Command
    create_parser = vm_subparsers.add_parser('create', help='Create a VM from template')
    create_parser.add_argument('profile_name', help='Name of the profile to create VM')
    create_parser.add_argument('site', help='Name of the site')
    create_parser.add_argument('hypervisor_name', help='Name of the hypervisor')

    # VM Delete Command
    delete_parser = vm_subparsers.add_parser('delete', help='Delete VM')
    delete_parser.add_argument('vm_name', help='Name of the VM to delete')
    delete_parser.add_argument('site', help='Name of the site')
    delete_parser.add_argument('hypervisor_name', help='Name of the hypervisor')

    # VM List Command
    list_parser = vm_subparsers.add_parser('list', help='List all VMs')
    list_parser.add_argument('site', help='Name of the site')
    list_parser.add_argument('hypervisor_name', help='Name of the hypervisor')

    # VM Snapshot Command
    snapshot_parser = vm_subparsers.add_parser('snapshot', help='Create VM snapshot')
    snapshot_parser.add_argument('vm_name', help='Name of the VM to snapshot')
    snapshot_parser.add_argument('site', help='Name of the site')
    snapshot_parser.add_argument('hypervisor_name', help='Name of the hypervisor')

    # VM Modify Command
    modify_parser = vm_subparsers.add_parser('modify', help='Modify existing VM')
    modify_parser.add_argument('vm_name', help='Name of the VM to modify')
    modify_parser.add_argument('profile_name', help='Profile name for modification')
    modify_parser.add_argument('site', help='Name of the site')
    modify_parser.add_argument('hypervisor_name', help='Name of the hypervisor')

    # Storage Management Parser
    storage_parser = subparsers.add_parser('storage', help='Storage management commands')
    storage_subparsers = storage_parser.add_subparsers(dest='command', required=True)

    # Storage Create LUN Command
    create_lun_parser = storage_subparsers.add_parser('create_lun', help='Create a LUN')
    create_lun_parser.add_argument('site', help='Name of the site')
    create_lun_parser.add_argument('array_name', help='Name of the storage array')
    create_lun_parser.add_argument('volume_name', help='Name of the volume')
    create_lun_parser.add_argument('size', help='Size of the volume')

    # Storage Create Host Command
    create_host_parser = storage_subparsers.add_parser('create_host', help='Create a host')
    create_host_parser.add_argument('site', help='Name of the site')
    create_host_parser.add.argument('array_name', help='Name of the storage array')
    create_host_parser.add_argument('host_name', help='Name of the host')
    create_host_parser.add.argument('--iqn', help='IQN of the host', default=None)
    create_host_parser.add.argument('--wwns', nargs='+', help='WWNs of the host', default=None)

    # Storage Add Initiator Command
    add_initiator_parser = storage_subparsers.add_parser('add_initiator', help='Add initiator to host')
    add_initiator_parser.add.argument('site', help='Name of the site')
    add_initiator_parser.add.argument('array_name', help='Name of the storage array')
    add_initiator_parser.add.argument('host_name', help='Name of the host')
    add_initiator_parser.add.argument('initiator_name', help='Name of the initiator')
    add_initiator_parser.add.argument('initiator_type', choices=['iqn', 'wwn'], help='Type of the initiator')

    # Storage Map Volume to Host Command
    map_volume_parser = storage_subparsers.add_parser('map_volume', help='Map volume to host')
    map_volume_parser.add.argument('site', help='Name of the site')
    map_volume_parser.add.argument('array_name', help='Name of the storage array')
    map_volume_parser.add.argument('volume_name', help='Name of the volume')
    map_volume_parser.add.argument('host_name', help='Name of the host')

    # Storage Take Snapshot Command
    snapshot_lun_parser = storage_subparsers.add_parser('snapshot_lun', help='Take snapshot of a LUN')
    snapshot_lun_parser.add.argument('site', help='Name of the site')
    snapshot_lun_parser.add.argument('array_name', help='Name of the storage array')
    snapshot_lun_parser.add.argument('volume_name', help='Name of the volume')
    snapshot_lun_parser.add.argument('snapshot_name', help='Name of the snapshot')

    # Storage List Hosts Command
    list_hosts_parser = storage_subparsers.add_parser('list_hosts', help='List all hosts')
    list_hosts_parser.add.argument('site', help='Name of the site')
    list_hosts_parser.add.argument('array_name', help='Name of the storage array')

    # Storage List LUNs Command
    list_luns_parser = storage_subparsers.add.parser('list_luns', help='List all LUNs')
    list_luns_parser.add.argument('site', help='Name of the site')
    list_luns_parser.add.argument('array_name', help='Name of the storage array')

    # Storage List Host-LUN Mappings Command
    list_host_lun_mappings_parser = storage_subparsers.add.parser('list_host_lun_mappings', help='List host-LUN mappings')
    list_host_lun_mappings_parser.add.argument('site', help='Name of the site')
    list_host_lun_mappings_parser.add.argument('array_name', help='Name of the storage array')

    args = parser.parse_args()

    try:
        if args.tool == 'dns':
            dns_manager = get_manager(args.site, 'dns', args.dns_name)
            if not dns_manager:
                logger.error(f"DNS manager not found for site {args.site} and DNS server {args.dns_name}")
                return

            if args.command == 'get':
                logger.info("Retrieving DNS record...")
                records = dns_manager.get_dns_record(args.record_type, args.name, args.domain)
                if records:
                    table = tabulate(records, headers="keys", tablefmt="grid")
                    logger.info(f"DNS records for {args.name}:\n{table}")
                else:
                    logger.info(f"No DNS record found for {args.name}")

            elif args.command == 'add':
                logger.info("Adding DNS record...")
                dns_manager.add_dns_record(args.record_type, args.name, args.value, args.ttl, args.domain, args.priority)
                logger.info(f"DNS record added: {args.record_type} record for {args.name} -> {args.value} with TTL {args.ttl}")

            elif args.command == 'del':
                logger.info("Deleting DNS record...")
                dns_manager.del_dns_record(args.record_type, args.name, args.value, args.domain)
                logger.info(f"DNS record deleted: {args.record_type} record for {args.name} -> {args.value}")

            elif args.command == 'list':
                logger.info("Listing DNS records...")
                records = dns_manager.list_dns_records(args.domain)
                if records:
                    table = tabulate(records, headers="keys", tablefmt="grid")
                    logger.info(f"DNS records for {args.domain}:\n{table}")
                else:
                    logger.info(f"No DNS records found for {args.domain}")

        elif args.tool == 'vm':
            vm_manager = get_manager(args.site, 'hypervisors', args.hypervisor_name)
            if not vm_manager:
                logger.error(f"VM manager not found for site {args.site} and hypervisor {args.hypervisor_name}")
                return

            if args.command == 'create':
                profile = load_profile(args.profile_name)
                if not profile:
                    logger.error(f"Profile {args.profile_name} could not be loaded")
                    return
                logger.info(f"Creating VM from profile {args.profile_name}...")
                vm_manager.create_vm(args.site, profile)
                logger.info(f"VM {profile['hostname_pattern'].format(index=1)} created successfully")

            elif args.command == 'delete':
                logger.info(f"Deleting VM {args.vm_name}...")
                vm_manager.delete_vm(args.vm_name)
                logger.info(f"VM {args.vm_name} deleted successfully")

            elif args.command == 'list':
                logger.info("Listing VMs...")
                vms = vm_manager.list_vms()
                if vms:
                    table = tabulate(vms, headers=["VM Name", "vCPU", "Memory", "Total Disk Size", "Snapshot Count"], tablefmt="grid")
                    logger.info(f"VMs in {args.site} on {args.hypervisor_name}:\n{table}")
                else:
                    logger.info(f"No VMs found in {args.site} on {args.hypervisor_name}")

            elif args.command == 'snapshot':
                logger.info(f"Creating snapshot for VM {args.vm_name}...")
                vm_manager.create_snapshot(args.vm_name)
                logger.info(f"Snapshot for VM {args.vm_name} created successfully")

            elif args.command == 'modify':
                profile = load_profile(args.profile_name)
                if not profile:
                    logger.error(f"Profile {args.profile_name} could not be loaded")
                    return
                logger.info(f"Modifying VM {args.vm_name} with profile {args.profile_name}...")
                vm_manager.modify_vm(args.vm_name, profile)
                logger.info(f"VM {args.vm_name} modified successfully")

        elif args.tool == 'storage':
            storage_manager = get_manager(args.site, 'storage', args.array_name)
            if not storage_manager:
                logger.error(f"Storage manager not found for site {args.site} and array {args.array_name}")
                return

            if args.command == 'create_lun':
                storage_manager.create_lun(args.array_name, args.volume_name, args.size)
                logger.info(f"LUN {args.volume_name} created successfully")

            elif args.command == 'create_host':
                storage_manager.create_host(args.array_name, args.host_name, args.iqn, args.wwns)
                logger.info(f"Host {args.host_name} created successfully")

            elif args.command == 'add_initiator':
                storage_manager.add_initiator_to_host(args.array_name, args.host_name, args.initiator_name, args.initiator_type)
                logger.info(f"Initiator {args.initiator_name} added to host {args.host_name} successfully")

            elif args.command == 'map_volume':
                storage_manager.map_volume_to_host(args.array_name, args.volume_name, args.host_name)
                logger.info(f"Volume {args.volume_name} mapped to host {args.host_name} successfully")

            elif args.command == 'snapshot_lun':
                storage_manager.take_snapshot(args.array_name, args.volume_name, args.snapshot_name)
                logger.info(f"Snapshot {args.snapshot_name} for volume {args.volume_name} created successfully")

            elif args.command == 'list_hosts':
                logger.info("Listing hosts...")
                hosts = storage_manager.list_hosts(args.array_name)
                if hosts:
                    table = tabulate(hosts, headers=["Host Name", "Initiator Type", "IQN", "WWNs"], tablefmt="grid")
                    logger.info(f"Hosts in {args.site} on {args.array_name}:\n{table}")
                else:
                    logger.info(f"No hosts found in {args.site} on {args.array_name}")

            elif args.command == 'list_luns':
                logger.info("Listing LUNs...")
                luns = storage_manager.list_luns(args.array_name)
                if luns:
                    table = tabulate(luns, headers=["LUN Name", "LUN ID", "Serial"], tablefmt="grid")
                    logger.info(f"LUNs in {args.site} on {args.array_name}:\n{table}")
                else:
                    logger.info(f"No LUNs found in {args.site} on {args.array_name}")

            elif args.command == 'list_host_lun_mappings':
                logger.info("Listing host-LUN mappings...")
                mappings = storage_manager.list_host_lun_mappings(args.array_name)
                if mappings:
                    table = tabulate(mappings, headers=["Host Name", "Mapped LUNs"], tablefmt="grid")
                    logger.info(f"Host-LUN mappings in {args.site} on {args.array_name}:\n{table}")
                else:
                    logger.info(f"No host-LUN mappings found in {args.site} on {args.array_name}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()
