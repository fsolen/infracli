from pyVim.connect import SmartConnect, Disconnect
import ssl
import yaml

class vCenterConnector:
    def __init__(self, config_file):
        self.config_file = config_file
        self.service_instance = None

    def connect(self):
        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)

        host = config['host']
        username = config['username']
        password = config['password']

        context = None
        if hasattr(ssl, "_create_unverified_context"):
            context = ssl._create_unverified_context()

        try:
            self.service_instance = SmartConnect(host=host,
                                               user=username,
                                               pwd=password,
                                               sslContext=context)
            return True
        except Exception as e:
            print("Unable to connect to vCenter:", str(e))
            return False

    def disconnect(self):
        try:
            if self.service_instance:
                Disconnect(self.service_instance)
                print("Disconnected from vCenter")
        except Exception as e:
            print("Error disconnecting from vCenter:", str(e))
