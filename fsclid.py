import argparse
import os
from tabulate import tabulate
import winrm

DNS_CONFIG_PATH = 'dnsserver_configs/dns_configs.txt'
WINRM_USER = 'username'
WINRM_PASS = 'password'

def run_winrm_command(command, dns_server):
    session = winrm.Session(f'http://{dns_server}:5985/wsman', auth=(WINRM_USER, WINRM_PASS))
    response = session.run_cmd(command)
    if response.status_code == 0:
        return response.std_out.decode()
    else:
        raise Exception(f"Error: {response.std_err.decode()}")

def load_dns_servers(domain):
    with open(DNS_CONFIG_PATH, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2 and parts[0] == domain:
                return parts[1]
    return None

def check_if_exists(record_type, name, dns_server):
    command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
    try:
        output = run_winrm_command(command, dns_server)
        return bool(output.strip())
    except Exception as e:
        print(f"Error checking if record exists: {e}")
        return False

def get_dns_record(record_type, name, dns_server):
    command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
    try:
        output = run_winrm_command(command, dns_server)
        print(output)
    except Exception as e:
        print(f"Error: {e}")

def add_dns_record(record_type, name, value, ttl, dns_server, priority=None):
    if check_if_exists(record_type, name, dns_server):
        confirm = input(f"{record_type} record for {name} already exists. Do you want to update it? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Add operation cancelled.")
            return
        del_dns_record(record_type, name, dns_server, priority)

    if record_type == 'A':
        command = f"Add-DnsServerResourceRecordA -ZoneName {dns_server} -Name {name} -IPv4Address {value} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
        ptr_command = f"Add-DnsServerResourceRecordPtr -ZoneName {dns_server} -Name {value} -PtrDomainName {name} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
    elif record_type == 'CNAME':
        command = f"Add-DnsServerResourceRecordCName -ZoneName {dns_server} -Name {name} -HostNameAlias {value} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
    elif record_type == 'TXT':
        command = f"Add-DnsServerResourceRecordTxt -ZoneName {dns_server} -Name {name} -DescriptiveText '{value}' -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
    elif record_type == 'MX':
        command = f"Add-DnsServerResourceRecordMX -ZoneName {dns_server} -Name {name} -MailExchange {value} -Preference {priority} -TimeToLive ([TimeSpan]::FromSeconds({ttl}))"
    else:
        print(f"Unsupported record type: {record_type}")
        return

    try:
        output = run_winrm_command(command, dns_server)
        print(output)
        if record_type == 'A':
            ptr_output = run_winrm_command(ptr_command, dns_server)
            print(ptr_output)
    except Exception as e:
        print(f"Error adding record: {e}")

def del_dns_record(record_type, name, value, dns_server, priority=None):
    if not check_if_exists(record_type, name, dns_server):
        print(f"{record_type} record for {name} does not exist.")
        return
    confirm = input(f"Are you sure you want to delete the {record_type} record for {name}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Delete operation cancelled.")
        return

    if record_type == 'A':
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType A -RecordData {value} -Force"
        ptr_command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {value} -RRType PTR -RecordData {name} -Force"
    elif record_type == 'CNAME':
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType CNAME -RecordData {value} -Force"
    elif record_type == 'TXT':
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType TXT -RecordData '{value}' -Force"
    elif record_type == 'MX':
        command = f"Remove-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType MX -RecordData {value} -Force"
    else:
        print(f"Unsupported record type: {record_type}")
        return

    try:
        output = run_winrm_command(command, dns_server)
        print(output)
        if record_type == 'A':
            ptr_output = run_winrm_command(ptr_command, dns_server)
            print(ptr_output)
    except Exception as e:
        print(f"Error deleting record: {e}")

def list_dns_records(dns_server):
    command = f"Get-DnsServerResourceRecord -ZoneName {dns_server}"
    try:
        output = run_winrm_command(command, dns_server)
        records = []
        for line in output.strip().split('\n'):
            parts = line.split()
            records.append(parts)
        print(tabulate(records, headers=['Type', 'Name', 'Value'], tablefmt='pretty'))
    except Exception as e:
        print(f"Error listing records: {e}")

def main():
    parser = argparse.ArgumentParser(description='Manage Microsoft DNS server records.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    dns_parser = subparsers.add_parser('dns', help='DNS related commands')
    dns_subparsers = dns_parser.add_subparsers(dest='dns_command', required=True)

    get_parser = dns_subparsers.add_parser('get', help='Get DNS record')
    get_parser.add_argument('record_type', choices=['A', 'CNAME', 'PTR', 'TXT', 'MX'], help='Type of DNS record')
    get_parser.add_argument('name', help='Name of the DNS record')
    get_parser.add_argument('domain', help='Domain name to get DNS server address')

    add_parser = dns_subparsers.add_parser('add', help='Add DNS record')
    add_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    add_parser.add_argument('name', help='Name of the DNS record')
    add_parser.add_argument('value', help='Value of the DNS record')
    add_parser.add_argument('--ttl', type=int, default=3600, help='Time to live of the DNS record')
    add_parser.add_argument('domain', help='Domain name to get DNS server address')
    add_parser.add_argument('--priority', type=int, help='Priority for MX record')

    del_parser = dns_subparsers.add_parser('del', help='Delete DNS record')
    del_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    del_parser.add_argument('name', help='Name of the DNS record')
    del_parser.add_argument('value', help='Value of the DNS record')
    del_parser.add_argument('domain', help='Domain name to get DNS server address')

    list_parser = dns_subparsers.add_parser('list', help='List all DNS records for a domain')
    list_parser.add_argument('domain', help='Domain name to get DNS server address')

    args = parser.parse_args()

    dns_server = load_dns_servers(args.domain)
    if not dns_server:
        print(f"DNS server not found for domain {args.domain}")
        return

    if args.command == 'dns':
        if args.dns_command == 'get':
            get_dns_record(args.record_type, args.name, dns_server)
        elif args.dns_command == 'add':
            add_dns_record(args.record_type, args.name, args.value, args.ttl, dns_server, args.priority)
        elif args.dns_command == 'del':
            del_dns_record(args.record_type, args.name, args.value, dns_server, args.priority)
        elif args.dns_command == 'list':
            list_dns_records(dns_server)

if __name__ == '__main__':
    main()

