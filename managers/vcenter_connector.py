import os
import ssl
import yaml
from pyVim.connect import SmartConnect, Disconnect
from .site_config import SiteConfig  # Import SiteConfig to load credentials

class vCenterConnector:
    def __init__(self, site_name, config_path):
        self.site_config = SiteConfig(config_path).get_site_config(site_name)
        self.service_instance = self.connect()

    def connect(self):
        host = self.site_config['vcenter']['host']
        username = self.site_config['vcenter']['username']
        password = self.site_config['vcenter']['password']
        context = None
        if hasattr(ssl, "_create_unverified_context"):
            context = ssl._create_unverified_context()
        try:
            return SmartConnect(host=host, user=username, pwd=password, sslContext=context)
        except Exception as e:
            print("Unable to connect to vCenter:", str(e))
            return None

    def disconnect(self):
        try:
            if self.service_instance:
                Disconnect(self.service_instance)
                print("Disconnected from vCenter")
        except Exception as e:
            print("Error disconnecting from vCenter:", str(e))
