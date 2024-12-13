import winrm

DNS_CONFIG_PATH = 'dnsserver_configs/dns_configs.txt'
WINRM_USER = 'username'
WINRM_PASS = 'password'

class DNSManager:
    @staticmethod
    def run_winrm_command(command, dns_server):
        session = winrm.Session(f'http://{dns_server}:5985/wsman', auth=(WINRM_USER, WINRM_PASS))
        response = session.run_cmd(command)
        if response.status_code == 0:
            return response.std_out.decode()
        else:
            raise Exception(f"Error: {response.std_err.decode()}")

    @staticmethod
    def load_dns_servers(domain):
        with open(DNS_CONFIG_PATH, 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 2 and parts[0] == domain:
                    return parts[1]
        return None

    def check_if_exists(self, record_type, name, dns_server):
        command = f"Get-DnsServerResourceRecord -ZoneName {dns_server} -Name {name} -RRType {record_type}"
        try:
            output = self.run_winrm_command(command, dns_server)
            return bool(output.strip())
        except Exception as e:
            print(f"Error checking if record exists: {e}")
            return False

    # Add other DNSManager methods here
