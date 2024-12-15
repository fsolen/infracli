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

    def create_host(self, array_name, host_name):
        array = self.arrays.get(array_name)
        if array:
            array.create_host(host_name)
            print(f"Host {host_name} created on {array_name}.")
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
            print(tabulate(hosts, headers="keys", tablefmt="grid"))
        else:
            print(f"Array {array_name} not found.")

    def list_luns(self, array_name):
        array = self.arrays.get(array_name)
        if array:
            volumes = array.list_volumes()
            mappings = array.list_host_connections()
            volume_table = []
            for volume in volumes:
                volume_name = volume['name']
                mapped_hosts = [mapping['host'] for mapping in mappings if mapping['vol'] == volume_name]
                volume_table.append({
                    'Volume Name': volume_name,
                    'Size': volume['size'],
                    'Mapped Hosts': ', '.join(mapped_hosts) if mapped_hosts else 'None'
                })
            print(tabulate(volume_table, headers="keys", tablefmt="grid"))
        else:
            print(f"Array {array_name} not found.")
