import argparse
from dns_manager import DNSManager
from vcenter_connector import vCenterConnector
from vm_manager import VMManager

def main():
    parser = argparse.ArgumentParser(description='Unified DNS and VM Management Tool')
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

    # VM Delete Command
    delete_parser = vm_subparsers.add_parser('delete', help='Delete VM')
    delete_parser.add_argument('vm_name', help='Name of the VM to delete')

    # VM List Command
    vm_subparsers.add_parser('list', help='List all VMs')

    # VM Snapshot Command
    snapshot_parser = vm_subparsers.add_parser('snapshot', help='Create VM snapshot')
    snapshot_parser.add_argument('vm_name', help='Name of the VM to snapshot')

    # VM Modify Command
    modify_parser = vm_subparsers.add_parser('modify', help='Modify existing VM')
    modify_parser.add_argument('vm_name', help='Name of the VM to modify')
    modify_parser.add_argument('profile_name', help='Profile name for modification')

    args = parser.parse_args()

    if args.tool == 'dns':
        dns_manager = DNSManager()
        dns_server = dns_manager.load_dns_servers(args.domain)
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
            dns_manager.list_dns_records(dns_server)

    elif args.tool == 'vm':
        vcenter_config_file = "hypervisor_configs/vmware/vcenter01_config.yaml"
        profiles_path = "vm_profiles"
        vcenter_connector = vCenterConnector(vcenter_config_file)
        if vcenter_connector.connect():
            vm_manager = VMManager(vcenter_connector.service_instance, profiles_path)

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

if __name__ == '__main__':
    main()
