import os
import yaml
import winrm

class DNSManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.dns_servers = self.load_dns_servers()

    def load_dns_servers(self):
        dns_servers = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as file:
                    config = yaml.safe_load(file)
                    domain = config['domain']
                    dns_server = config['dns_server']
                    dns_servers[domain] = dns_server
        return dns_servers

    def run_winrm_command(self, command, dns_server):
        session = winrm.Session(f'http://{dns_server}:5985/wsman', auth=(WINRM_USER, WINRM_PASS))
        response = session.run_cmd(command)
        if response.status_code == 0:
            return response.std_out.decode()
        else:
            raise Exception(f"Error: {response.std_err.decode()}")

    def get_dns_server(self, domain):
        return self.dns_servers.get(domain)

    def check_if_exists(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        try:
            output = self.run_winrm_command(command, dns_server)
            return bool(output.strip())
        except Exception as e:
            print(f"Error checking if record exists: {e}")
            return False

    def get_dns_record(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        try:
            output = self.run_winrm_command(command, dns_server)
            print(output)
        except Exception as e:
            print(f"Error: {e}")

    def add_dns_record(self, record_type, name, value, ttl, dns_server, priority=None):
        if self.check_if_exists(record_type, name, dns_server):
            confirm = input(f"{record_type} record for {name} already exists. Do you want to update it? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Add operation cancelled.")
                return
            self.del_dns_record(record_type, name, value, dns_server, priority)

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
            output = self.run_winrm_command(command, dns_server)
            print(output)
            if record_type == 'A':
                ptr_output = self.run_winrm_command(ptr_command, dns_server)
                print(ptr_output)
        except Exception as e:
            print(f"Error adding record: {e}")

    def del_dns_record(self, record_type, name, value, dns_server, priority=None):
        if not self.check_if_exists(record_type, name, dns_server):
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
            output = self.run_winrm_command(command, dns_server)
            print(output)
            if record_type == 'A':
                ptr_output = self.run_winrm_command(ptr_command, dns_server)
                print(ptr_output)
        except Exception as e:
            print(f"Error deleting record: {e}")

    def list_dns_records(self, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server}"
        try:
            output = self.run_winrm_command(command, dns_server)
            records = []
            for line in output.strip().split('\n'):
                parts = line.split()
                records.append(parts)
            print(tabulate(records, headers=['Type', 'Name', 'Value'], tablefmt='pretty'))
        except Exception as e:
            print(f"Error listing records: {e}")
