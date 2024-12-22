import os
import yaml
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from .phpipam_manager import PhpIpamManager

class VMManager:
    def __init__(self, service_instance, profiles_path, config_path):
        self.service_instance = service_instance
        self.profiles_path = profiles_path
        self.profiles = self.load_profiles()
        self.phpipam_manager = PhpIpamManager(config_path)

    def load_profiles(self):
        profiles = {}
        for filename in os.listdir(self.profiles_path):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(self.profiles_path, filename), 'r') as f:
                        profile = yaml.safe_load(f)
                        profile_name = os.path.splitext(filename)[0]
                        profiles[profile_name] = profile
                except Exception as e:
                    print(f"Error loading profile {filename}: {str(e)}")
        return profiles

    def select_host(self):
        content = self.service_instance.RetrieveContent()
        hosts = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view
        selected_host = None
        min_cpu = float('inf')
        min_memory = float('inf')

        for host in hosts:
            host_summary = host.summary
            if host_summary.runtime.connectionState == "connected":
                cpu_usage = host_summary.quickStats.overallCpuUsage
                memory_usage = host_summary.quickStats.overallMemoryUsage
                if cpu_usage < min_cpu and memory_usage < min_memory:
                    min_cpu = cpu_usage
                    min_memory = memory_usage
                    selected_host = host

        return selected_host

    def select_datastore(self, host):
        datastore = None
        max_free_space = 0

        for ds in host.datastore:
            summary = ds.summary
            free_space = summary.freeSpace

            if free_space > max_free_space:
                max_free_space = free_space
                datastore = ds

        return datastore

    def get_all_snapshots_names(self, snapshots):
        snapshot_names = []
        for snapshot in snapshots:
            snapshot_names.append(snapshot.name)
            if snapshot.childSnapshotList:
                snapshot_names.extend(self.get_all_snapshots_names(snapshot.childSnapshotList))
        return snapshot_names

    def create_vm(self, cluster_name, profile_name):
        try:
            content = self.service_instance.RetrieveContent()
            profile = self.profiles.get(profile_name)

            if not profile:
                raise ValueError(f"Profile {profile_name} not found")

            ip_address = self.phpipam_manager.get_next_available_ip(profile['vlan'])

            datacenter = content.rootFolder.childEntity[0]
            vm_folder = datacenter.vmFolder

            # Find the template VM
            template_name = profile.get('template_name', '')  # Get template name from profile
            template_vm = None
            template_folder = None
            for child in vm_folder.childEntity:
                if isinstance(child, vim.Folder) and child.name == "Templates":
                    template_folder = child
                    break

            if not template_folder:
                raise ValueError("Template folder not found")

            for template_child in template_folder.childEntity:
                if isinstance(template_child, vim.VirtualMachine) and template_child.name == template_name:
                    template_vm = template_child
                    break

            if not template_vm:
                raise ValueError(f"Template VM {template_name} not found")

            # Generate a new unique VM name
            index = 1
            new_vm_name = profile['hostname_pattern'].format(index=index)
            while get_vm_by_name(new_vm_name, content):
                index += 1
                new_vm_name = profile['hostname_pattern'].format(index=index)

            # Select host with least CPU and memory usage
            host = self.select_host()

            # Select datastore with most available free space
            datastore = self.select_datastore(host)

            # Find the resource pool
            resource_pool = host.parent.resourcePool

            # Clone specification
            clone_spec = vim.vm.CloneSpec(location=vim.vm.RelocateSpec(datastore=datastore, pool=resource_pool),
                                          powerOn=False, template=False)

            # Clone the VM from the template
            task = template_vm.Clone(folder=vm_folder, name=new_vm_name, spec=clone_spec)
            print("Cloning VM from template...")

            timeout = 600  # Timeout in seconds
            start_time = time.time()

            while task.info.state == vim.TaskInfo.State.running:
                if time.time() - start_time > timeout:
                    print("Error: Task timed out")
                    break
                time.sleep(5)  # Sleep for 5 seconds before checking again

            if task.info.state == vim.TaskInfo.State.success:
                print(f"VM {new_vm_name} created successfully")
            else:
                print(f"Error creating VM: {task.info.error}")

def get_vm_by_name(vm_name, content):
    vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view
    for vm in vm_list:
        if vm.name == vm_name:
            return vm
    return None
s
