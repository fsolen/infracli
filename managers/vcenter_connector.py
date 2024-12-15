import os
import ssl
import yaml
from pyVim.connect import SmartConnect, Disconnect

class vCenterConnector:
    def __init__(self, config_path):
        self.config_path = config_path
        self.vcenters = self.load_vcenters()

    def load_vcenters(self):
        vcenters = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    config = yaml.safe_load(f)
                    vcenter_name = os.path.splitext(filename)[0]
                    vcenters[vcenter_name] = config
        return vcenters

    def connect(self, vcenter_name):
        config = self.vcenters.get(vcenter_name)
        if not config:
            print(f"vCenter configuration for {vcenter_name} not found.")
            return False

        host = config['host']
        username = config['username']
        password = config['password']

        context = None
        if hasattr(ssl, "_create_unverified_context"):
            context = ssl._create_unverified_context()

        try:
            self.service_instance = SmartConnect(host=host, user=username, pwd=password, sslContext=context)
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
