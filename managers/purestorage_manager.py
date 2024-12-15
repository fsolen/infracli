import os
import yaml
from purestorage import FlashArray
from tabulate import tabulate

class StorageManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.arrays = self.load_arrays()

    def load_arrays(self):
        arrays = {}
        for filename in os.listdir(self.config_path):
            if filename.endswith(".yaml"):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    config = yaml.safe_load(f)
                    array_name = os.path.splitext(filename)[0]
                    arrays[array_name] = FlashArray(config['pure_fa_api_url'], api_token=config['pure_fa_api_token'])
        return arrays

    def create_lun(self, array_name, volume_name, size):
        array = self.arrays.get(array_name)
        if array:
            array.create_volume(volume_name, size)
            print(f"LUN {volume_name} created on {array_name} with size {size}.")
        else:
            print(f"Array {array_name} not found.")

    def create_host(self, array_name, host_name, iqn=None, wwns=None):
        array = self.arrays.get(array_name)
        if array:
            if iqn or (wwns and len(wwns) >= 2):
                array.create_host(host_name, iqnlist=[iqn] if iqn else None, wwnlist=wwns if wwns else None)
                print(f"Host {host_name} created on {array_name} with IQN {iqn} and WWNs {wwns}.")
            else:
                print("Host must have an IQN or at least two WWNs.")
        else:
            print(f"Array {array_name} not found.")

    def add_initiator_to_host(self, array_name, host_name, initiator_name, initiator_type):
        array = self.arrays.get(array_name)
        if array:
            if initiator_type == 'iqn':
                array.set_host(host_name, iqnlist=[initiator_name])
                print(f"IQN {initiator_name} added to host {host_name} on {array_name}.")
            elif initiator_type == 'wwn':
                array.set_host(host_name, wwnlist=[initiator_name])
                print(f"WWN {initiator_name} added to host {host_name} on {array_name}.")
            else:
                print(f"Invalid initiator type: {initiator_type}. Must be 'iqn' or 'wwn'.")
        else:
            print(f"Array {array_name} not found.")

    def map_volume_to_host(self, array_name, volume_name, host_name):
        array = self.arrays.get(array_name)
        if array:
            array.connect_host(host_name, volume_name)
            print(f"Volume {volume_name} mapped to host {host_name} on {array_name}.")
        else:
            print(f"Array {array_name} not found.")

    def take_snapshot(self, array_name, volume_name, snapshot_name):
        array = self.arrays.get(array_name)
        if array:
            array.create_snapshot(volume_name, suffix=snapshot_name)
            print(f"Snapshot {snapshot_name} taken for volume {volume_name} on {array_name}.")
        else:
            print(f"Array {array_name} not found.")

    def list_hosts(self, array_name):
        array = self.arrays.get(array_name)
        if array:
            hosts = array.list_hosts()
            formatted_hosts = [
                {
                    "Name": host["name"],
                    "IQNs": ", ".join(host.get("iqn", [])),
                    "WWNs": ", ".join(host.get("wwn", []))
                }
                for host in hosts
            ]
            print(tabulate(formatted_hosts, headers="keys"))
        else:
            print(f"Array {array_name} not found.")

    def list_luns(self, array_name):
        array = self.arrays.get(array_name)
        if array:
            luns = array.list_volumes()
            print(tabulate(luns, headers="keys"))
        else:
            print(f"Array {array_name} not found.")

    def list_host_lun_mappings(self, array_name):
        array = self.arrays.get(array_name)
        if array:
            mappings = []
            hosts = array.list_hosts()
            for host in hosts:
                host_name = host["name"]
                volumes = array.list_host_connections(host_name)
                for volume in volumes:
                    mappings.append({
                        "Host": host_name,
                        "Volume": volume["vol"],
                        "LUN": volume["lun"]
                    })
            print(tabulate(mappings, headers="keys"))
        else:
            print(f"Array {array_name} not found.")
