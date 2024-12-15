import argparse
import os
import yaml
from dns_manager import DNSManager
from vcenter_connector import vCenterConnector
from vm_manager import VMManager
from storage_manager import StorageManager
from harvester_manager import HarvesterManager

def main():
    parser = argparse.ArgumentParser(description='Unified DNS, VM, and Storage Management Tool')
    subparsers = parser.add_subparsers(dest='tool', required=True)

    # DNS Management Parser
    dns_parser = subparsers.add_parser('dns', help='DNS management commands')
    dns_subparsers = dns_parser.add_subparsers(dest='command', required=True)

    # DNS Get Command
    get_parser = dns_subparsers.add_parser('get', help='Get DNS record')
    get_parser.add_argument('record_type', choices=['A', 'CNAME', 'PTR', 'TXT', 'MX'], help='Type of DNS record')
    get_parser.add_argument('name', help='Name of the DNS record')
    get_parser.add_argument('domain', help='Domain name to get DNS server address')

    # DNS Add Command
    add_parser = dns_subparsers.add_parser('add', help='Add DNS record')
    add_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    add_parser.add_argument('name', help='Name of the DNS record')
    add_parser.add_argument('value', help='Value of the DNS record')
    add_parser.add_argument('--ttl', type=int, default=3600, help='Time to live of the DNS record')
    add_parser.add_argument('domain', help='Domain name to get DNS server address')
    add_parser.add_argument('--priority', type=int, help='Priority for MX record')

    # DNS Delete Command
    del_parser = dns_subparsers.add_parser('del', help='Delete DNS record')
    del_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    del_parser.add_argument('name', help='Name of the DNS record')
    del_parser.add_argument('value', help='Value of the DNS record')
    del_parser.add_argument('domain', help='Domain name to get DNS server address')

    # DNS List Command
    list_parser = dns_subparsers.add_parser('list', help='List all DNS records')
    list_parser.add_argument('domain', help='Domain name to get DNS server address')

    # VM Management Parser
    vm_parser = subparsers.add_parser('vm', help='VM management commands')
    vm_subparsers = vm_parser.add_subparsers(dest='command', required=True)

    # VM Create Command
    create_parser = vm_subparsers.add_parser('create', help='Create a VM from template')
    create_parser.add_argument('profile_name', help='Name of the profile to create VM')
    create_parser.add_argument('vcenter_name', help='Name of the vCenter configuration')

    # VM Delete Command
    delete_parser = vm_subparsers.add_parser('delete', help='Delete VM')
    delete_parser.add_argument('vm_name', help='Name of the VM to delete')
    delete_parser.add_argument('vcenter_name', help='Name of the vCenter configuration')

    # VM List Command
    list_parser = vm_subparsers.add_parser('list', help='List all VMs')
    list_parser.add_argument('vcenter_name', help='Name of the vCenter configuration')

    # VM Snapshot Command
    snapshot_parser = vm_subparsers.add_parser('snapshot', help='Create VM snapshot')
    snapshot_parser.add_argument('vm_name', help='Name of the VM to snapshot')
    snapshot_parser.add_argument('vcenter_name', help='Name of the vCenter configuration')

    # VM Modify Command
    modify_parser = vm_subparsers.add_parser('modify', help='Modify existing VM')
    modify_parser.add_argument('vm_name', help='Name of the VM to modify')
    modify_parser.add_argument('profile_name', help='Profile name for modification')
    modify_parser.add_argument('vcenter_name', help='Name of the vCenter configuration')

    # Storage Management Parser
    storage_parser = subparsers.add_parser('storage', help='Storage management commands')
    storage_subparsers = storage_parser.add_subparsers(dest='command', required=True)

    # Storage Create LUN Command
    create_lun_parser = storage_subparsers.add_parser('create_lun', help='Create a LUN')
    create_lun_parser.add_argument('array_name', help='Name of the storage array')
    create_lun_parser.add_argument('volume_name', help='Name of the volume')
    create_lun_parser.add_argument('size', help='Size of the volume')

    # Storage Create Host Command
    create_host_parser = storage_subparsers.add_parser('create_host', help='Create a host')
    create_host_parser.add_argument('array_name', help='Name of the storage array')
    create_host_parser.add_argument('host_name', help='Name of the host')

    # Storage Map Volume to Host Command
    map_volume_parser = storage_subparsers.add_parser('map_volume', help='Map volume to host')
    map_volume_parser.add_argument('array_name', help='Name of the storage array')
    map_volume_parser.add_argument('volume_name', help='Name of the volume')
    map_volume_parser.add_argument('host_name', help='Name of the host')

    # Storage Take Snapshot Command
    snapshot_lun_parser = storage_subparsers.add_parser('snapshot_lun', help='Take snapshot of a LUN')
    snapshot_lun_parser.add_argument('array_name', help='Name of the storage array')
    snapshot_lun_parser.add_argument('volume_name', help='Name of the volume')
    snapshot_lun_parser.add_argument('snapshot_name', help='Name of the snapshot')

    # Storage List Hosts Command
    list_hosts_parser = storage_subparsers.add_parser('list_hosts', help='List all hosts')
    list_hosts_parser.add_argument('array_name', help='Name of the storage array')

    # Storage List LUNs Command
    list_luns_parser = storage_subparsers.add_parser('list_luns', help='List all LUNs')
    list_luns_parser.add_argument('array_name', help='Name of the storage array')

    args = parser.parse_args()

    if args.tool == 'dns':
        dns_manager = DNSManager(config_path="dnsserver_configs")
        dns_server = dns_manager.get_dns_server(args.domain)
        if not dns_server:
            print(f"DNS server not found for domain {args.domain}")
            return

        if args.command == 'get':
            dns_manager.get_dns_record(args.record_type, args.name, dns_server)
        elif args.command == 'add':
            dns_manager.add_dns_record(args.record_type, args.name, args.value, args.ttl, dns_server, args.priority)
        elif args.command == 'del':
            dns_manager.del_dns_record(args.record_type, args.name, args.value, dns_server)
        elif args.command == 'list':
            dns_manager.list_dns_records(args.domain)

    elif args.tool == 'vm':
        vcenter_connector = vCenterConnector(config_path="hypervisor_configs/vmware")
        if vcenter_connector.connect(args.vcenter_name):
            vm_manager = VMManager(vcenter_connector.service_instance, "vm_profiles")

            if args.command == 'create':
                vm_manager.create_vm(args.profile_name)
            elif args.command == 'delete':
                vm_manager.delete_vm(args.vm_name)
            elif args.command == 'list':
                vm_manager.list_vms()
            elif args.command == 'snapshot':
                vm_manager.create_snapshot(args.vm_name)
            elif args.command == 'modify':
                vm_manager.modify_vm(args.vm_name, args.profile_name)

            vcenter_connector.disconnect()
        else:
            print("Failed to connect to vCenter")

    elif args.tool == 'storage':
        storage_manager = StorageManager(config_path="storage_configs")

        if args.command == 'create_lun':
            storage_manager.create_lun(args.array_name, args.volume_name, args.size)
        elif args.command == 'create_host':
            storage_manager.create_host(args.array_name, args.host_name)
        elif args.command == 'map_volume':
            storage_manager.map_volume_to_host(args.array_name, args.volume_name, args.host_name)
        elif args.command == 'snapshot_lun':
            storage_manager.take_snapshot(args.array_name, args.volume_name, args.snapshot_name)
        elif args.command == 'list_hosts':
            storage_manager.list_hosts(args.array_name)
        elif args.command == 'list_luns':
            storage_manager.list_luns(args.array_name)

    elif args.tool == 'hrv':
        harvester_manager = HarvesterManager(config_path="hypervisor_configs/harvester")

        if args.command == 'create':
            profile_path = os.path.join("vm_profiles", f"{args.profile_name}.yaml")
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
            harvester_manager.create_vm(args.cluster_name, profile)
        elif args.command == 'delete':
            harvester_manager.delete_vm(args.cluster_name, args.vm_name)
        elif args.command == 'list':
            harvester_manager.list_vms(args.cluster_name)
        elif args.command == 'modify':
            profile_path = os.path.join("vm_profiles", f"{args.profile_name}.yaml")
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
            harvester_manager.modify_vm(args.cluster_name, args.vm_name, profile)

if __name__ == '__main__':
    main()
