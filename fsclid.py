import argparse
import dns.query
import dns.update
import dns.resolver
import os
from tabulate import tabulate

DNS_CONFIG_PATH = 'dnsserver_configs/dns_configs.txt'

def load_dns_servers(domain):
    with open(DNS_CONFIG_PATH, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2 and parts[0] == domain:
                return parts[1]
    return None

def check_if_exists(record_type, name, dns_server):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    try:
        answers = resolver.resolve(name, record_type)
        return True
    except dns.resolver.NoAnswer:
        return False
    except dns.resolver.NXDOMAIN:
        return False
    except Exception as e:
        print(f"Error checking if record exists: {e}")
        return False

def get_dns_record(record_type, name, dns_server):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    try:
        answers = resolver.resolve(name, record_type)
        for rdata in answers:
            print(f'{name} {record_type} {rdata}')
    except Exception as e:
        print(f"Error: {e}")

def add_dns_record(record_type, name, value, ttl, dns_server, priority=None):
    if check_if_exists(record_type, name, dns_server):
        confirm = input(f"{record_type} record for {name} already exists. Do you want to update it? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Add operation cancelled.")
            return
    update = dns.update.Update(dns_server)
    if record_type == 'A':
        update.replace(name, ttl, 'A', value)
        # Automatically add PTR record for A record
        ptr_name = '.'.join(reversed(value.split('.'))) + '.in-addr.arpa'
        update.replace(ptr_name, ttl, 'PTR', name)
    elif record_type == 'CNAME':
        update.replace(name, ttl, 'CNAME', value)
    elif record_type == 'TXT':
        update.replace(name, ttl, 'TXT', value)
    elif record_type == 'MX':
        if priority is None:
            print("MX record requires a priority value.")
            return
        update.replace(name, ttl, 'MX', priority, value)
    else:
        print(f"Unsupported record type: {record_type}")
        return
    response = dns.query.tcp(update, dns_server)
    print(response)

def del_dns_record(record_type, name, value, dns_server, priority=None):
    if not check_if_exists(record_type, name, dns_server):
        print(f"{record_type} record for {name} does not exist.")
        return
    confirm = input(f"Are you sure you want to delete the {record_type} record for {name}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Delete operation cancelled.")
        return
    update = dns.update.Update(dns_server)
    if record_type == 'A':
        update.delete(name, 'A', value)
        # Automatically delete PTR record for A record
        ptr_name = '.'.join(reversed(value.split('.'))) + '.in-addr.arpa'
        update.delete(ptr_name, 'PTR', name)
    elif record_type == 'CNAME':
        update.delete(name, 'CNAME', value)
    elif record_type == 'TXT':
        update.delete(name, 'TXT', value)
    elif record_type == 'MX':
        update.delete(name, 'MX', priority, value)
    else:
        print(f"Unsupported record type: {record_type}")
        return
    response = dns.query.tcp(update, dns_server)
    print(response)

def list_dns_records(domain, dns_server):
    record_types = ['A', 'CNAME', 'PTR', 'TXT', 'MX']
    records = []
    for record_type in record_types:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            answers = resolver.resolve(domain, record_type)
            for rdata in answers:
                records.append([record_type, domain, rdata.to_text()])
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue
        except Exception as e:
            print(f"Error: {e}")
            continue
    print(tabulate(records, headers=['Type', 'Name', 'Value'], tablefmt='pretty'))

def main():
    parser = argparse.ArgumentParser(description='Manage Microsoft DNS server records.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    get_parser = subparsers.add_parser('get', help='Get DNS record')
    get_parser.add_argument('record_type', choices=['A', 'CNAME', 'PTR', 'TXT', 'MX'], help='Type of DNS record')
    get_parser.add_argument('name', help='Name of the DNS record')
    get_parser.add_argument('domain', help='Domain name to get DNS server address')

    add_parser = subparsers.add_parser('add', help='Add DNS record')
    add_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    add_parser.add_argument('name', help='Name of the DNS record')
    add_parser.add_argument('value', help='Value of the DNS record')
    add_parser.add_argument('--ttl', type=int, default=3600, help='Time to live of the DNS record')
    add_parser.add_argument('domain', help='Domain name to get DNS server address')
    add_parser.add_argument('--priority', type=int, help='Priority for MX record')

    del_parser = subparsers.add_parser('del', help='Delete DNS record')
    del_parser.add_argument('record_type', choices=['A', 'CNAME', 'TXT', 'MX'], help='Type of DNS record')
    del_parser.add_argument('name', help='Name of the DNS record')
    del_parser.add_argument('value', help='Value of the DNS record')
    del_parser.add_argument('domain', help='Domain name to get DNS server address')
    del_parser.add_argument('--priority', type=int, help='Priority for MX record')

    list_parser = subparsers.add_parser('list', help='List all DNS records for a domain')
    list_parser.add_argument('domain', help='Domain name to get DNS server address')

    args = parser.parse_args()
    dns_server = load_dns_servers(args.domain)
    if not dns_server:
        print(f"No DNS server found for domain: {args.domain}")
        return

    if args.command == 'get':
        get_dns_record(args.record_type, args.name, dns_server)
    elif args.command == 'add':
        add_dns_record(args.record_type, args.name, args.value, args.ttl, dns_server, args.priority)
    elif args.command == 'del':
        del_dns_record(args.record_type, args.name, args.value, dns_server, args.priority)
    elif args.command == 'list':
        list_dns_records(args.domain, dns_server)

if __name__ == '__main__':
    main()
