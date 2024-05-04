## VM Management CLI
## 04.04.2024
## Credits Fatih Solen
## root@fatihsolen.com

import argparse
import yaml
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from prettytable import PrettyTable
import ssl
import os
import time

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

class VMManager:
    def __init__(self, service_instance, profiles_path):
        self.service_instance = service_instance
        self.profiles_path = profiles_path

    def load_profiles(self):
        self.profiles = {}
        for filename in os.listdir(self.profiles_path):
            if filename.endswith(".yaml"):
                profile_name = os.path.splitext(filename)[0]
                with open(os.path.join(self.profiles_path, filename), 'r') as f:
                    profile_data = yaml.safe_load(f)
                    self.profiles[profile_name] = profile_data

    def select_host(self):
        content = self.service_instance.RetrieveContent()
        hosts = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view
        selected_host = None
        min_cpu = float('inf')
        min_memory = float('inf')

        for host in hosts:
            host_summary = host.summary
            if host_summary.runtime.connectionState == "connected":
                if host_summary.quickStats.overallCpuUsage < min_cpu:
                    min_cpu = host_summary.quickStats.overallCpuUsage
                    selected_host = host
                if host_summary.quickStats.overallMemoryUsage < min_memory:
                    min_memory = host_summary.quickStats.overallMemoryUsage
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

    def create_vm(self, profile_name):
        try:
            content = self.service_instance.RetrieveContent()
            profile = self.profiles.get(profile_name)

            if not profile:
                print("Profile not found:", profile_name)
                return

            datacenter = content.rootFolder.childEntity[0]
            vm_folder = datacenter.vmFolder

            # Find the template VM
            template_name = profile.get('template_name', '')  # Get template name from profile
            template_vm = None
            template_folder = None
            for child in vm_folder.childEntity:
                if isinstance(child, vim.Folder) and child.name == "_Templates":
                    template_folder = child
                    break

            if not template_folder:
                print("Template folder '_Templates' not found.")
                return

            for template_child in template_folder.childEntity:
                if isinstance(template_child, vim.VirtualMachine) and template_child.name == template_name:
                    template_vm = template_child
                    break

            if not template_vm:
                print("Template VM '{}' not found in '_Templates' folder.".format(template_name))
                return

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

            while task.info.state == vim.TaskInfo.State.running:
                time.sleep(10)

            if task.info.state == vim.TaskInfo.State.running:
                # Check if the new VM exists
                new_vm = get_vm_by_name(new_vm_name, content)
                if new_vm:
                    print("VM cloned successfully with name:", new_vm_name)
                    self.modify_vm(new_vm_name, profile_name)
                else:
                    print("Failed to find the newly cloned VM:", new_vm_name)
            else:
                print("Failed to clone VM. Task state:", task.info.state)

        except Exception as e:
            print("Error creating VM:", str(e))

    def delete_vm(self, vm_name):
        try:
            content = self.service_instance.RetrieveContent()

            # Check if the VM exists
            vm = get_vm_by_name(vm_name, content)
            if not vm:
                print("VM '{}' not found.".format(vm_name))
                return

            # Prompt for confirmation
            confirmation = input("Are you sure you want to delete VM '{}'? (type 'yes' to confirm): ".format(vm_name))
            if confirmation.lower() != "yes":
                print("VM deletion cancelled.")
                return

            # Verify VM name / confirm twice
            vm_name_confirm = input("Please enter the exact name of the VM to confirm deletion: ")
            if vm_name_confirm != vm_name:
                print("Entered VM name does not match the actual name of the VM. Deletion cancelled.")
                return

            # Delete the VM
            print("Deleting VM...")
            task = vm.Destroy_Task()
            self.wait_for_task(task)
            print("VM deleted successfully.")

        except Exception as e:
            print("Error deleting VM:", str(e))


    def list_vms(self):
        try:
            content = self.service_instance.RetrieveContent()

            # Create a table
            table = PrettyTable()
            table.field_names = ["VM Name", "Total vCPU", "Total Memory (GB)", "Total Disk (GB)", "Network PortGroup", "Snapshots", "ESXi Hostname", "Cluster Name"]

            # Get all VMs
            vms = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view

            for vm in vms:
                # Get VM attributes
                vm_name = vm.name
                total_vcpu = vm.summary.config.numCpu
                total_memory_gb = vm.summary.config.memorySizeMB / 1024
                total_disk_gb = sum([disk.capacityInKB for disk in vm.config.hardware.device if isinstance(disk, vim.vm.device.VirtualDisk)]) / 1024 / 1024
                network_portgroup = ', '.join([nic.backing.network.name for nic in vm.config.hardware.device if isinstance(nic, vim.vm.device.VirtualEthernetCard) and hasattr(nic.backing, 'network')])
                esxi_hostname = vm.runtime.host.name
                cluster_name = vm.runtime.host.parent.name
                if vm.snapshot:
                    snapshot_names = self.get_all_snapshots_names(vm.snapshot.rootSnapshotList)
                    snapshots = ", ".join(snapshot_names)
                else:
                    snapshots = None

                # Add VM data to table
                table.add_row([vm_name, total_vcpu, total_memory_gb, round(total_disk_gb, 2), network_portgroup, snapshots, esxi_hostname, cluster_name])

            # Print the table
            print(table)

        except Exception as e:
            print("Error listing VMs:", str(e))

    def create_snapshot(self, vm_name):
        try:
            content = self.service_instance.RetrieveContent()
            vm = get_vm_by_name(vm_name, content)

            if vm:
                task = vm.CreateSnapshot_Task(name="snapshot_" + vm_name, description="Snapshot created by fsc", memory=False, quiesce=False)
                print("Creating snapshot...")
                self.wait_for_task(task)
                print("Snapshot created successfully for VM:", vm_name)
            else:
                print("VM not found with name:", vm_name)

        except Exception as e:
            print("Error creating snapshot:", str(e))

    def wait_for_task(self, task):
        """Waits for the task to complete."""
        while task.info.state == vim.TaskInfo.State.running:
            time.sleep(1)

        if task.info.state == vim.TaskInfo.State.success:
            print("Task completed successfully.")
        else:
            print("Task state:", task.info.state)
    
    def get_network_by_name(self, network_name, content):
        view = content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True)
        for network in view.view:
            if network.name == network_name:
                return network
        return None

    def modify_vm(self, vm_name, profile_name):
        try:
            content = self.service_instance.RetrieveContent()
            profile = self.profiles.get(profile_name)
    
            if not profile:
                print("Profile not found:", profile_name)
                return
    
            # Get the VM by name
            vm = get_vm_by_name(vm_name, content)
    
            if not vm:
                print("VM not found with name:", vm_name)
                return
    
            # Check if the VM is powered on
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                confirmation = input("The VM '{}' is currently powered on. Do you want to shut it down gracefully before modifying it? (yes/no): ".format(vm_name))
                if confirmation.lower() == "yes":
                    task = vm.ShutdownGuest()
                    self.wait_for_task(task)
                else:
                    print("Modification cancelled.")
                    return

            # Initialize the VM configuration specification
            spec = vim.vm.ConfigSpec()
  
            # Apply CPU and memory configurations from the profile
            spec.numCPUs = profile.get('cpu', vm.config.hardware.numCPU)
            spec.memoryMB = profile.get('memory', vm.config.hardware.memoryMB)
            
            # Update disk configurations from the profile
            spec.deviceChange = []
            for disk_spec in profile.get('disks', []):
                disk_name = disk_spec.get('name')
                disk_size_gb = disk_spec.get('size_gb')
                disk_found = False
            
                # Check if the disk specified in the profile exists in the VM's configuration
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualDisk) and device.deviceInfo.label == disk_name:
                        disk_found = True
            
                        # Modify the existing disk configuration
                        disk_change_spec = vim.vm.device.VirtualDeviceSpec()
                        disk_change_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        disk_change_spec.device = device
                        disk_change_spec.device.capacityInKB = disk_size_gb * 1024 * 1024
                        spec.deviceChange.append(disk_change_spec)
                        break
            
                # If the disk specified in the profile is not found, add it to the VM's configuration
                if not disk_found:
                    print("You specified in the profile '{}', but the VM does not have a disk named '{}'.".format(disk_name, disk_name))
                    print("Adding disk '{}' with size {} GB to the VM.".format(disk_name, disk_size_gb))
            
                    # Create a new disk device
                    new_disk = vim.vm.device.VirtualDisk()
                    new_disk.capacityInKB = disk_size_gb * 1024 * 1024
            
                    # Find or create a SCSI controller
                    controller = None
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualSCSIController):
                            controller = device
                            break
            
                    if not controller:
                        # Create a new SCSI controller
                        controller_spec = vim.vm.device.VirtualDeviceSpec()
                        controller_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                        controller_spec.device = vim.vm.device.VirtualLsiLogicController()
                        controller_spec.device.key = 1000
                        controller_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
                        controller_spec.device.busNumber = 0
                        controller_spec.device.hotAddRemove = True
                        spec.deviceChange.append(controller_spec)
                        controller = controller_spec.device
            
                    # Configure disk backing
                    disk_backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                    disk_backing.diskMode = 'persistent'
                    disk_backing.fileName = ''
                    new_disk.backing = disk_backing
            
                    # Assign the new disk to the controller
                    new_disk.unitNumber = len([dev for dev in vm.config.hardware.device if isinstance(dev, vim.vm.device.VirtualDisk)])
                    new_disk.controllerKey = controller.key
            
                    # Create a new disk addition specification
                    new_disk_spec = vim.vm.device.VirtualDeviceSpec()
                    new_disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
                    new_disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                    new_disk_spec.device = new_disk
            
                    # Add the disk addition specification to the VM configuration
                    spec.deviceChange.append(new_disk_spec)
   
            # Change network port group (VLAN)
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    network_spec = vim.vm.device.VirtualDeviceSpec()
                    network_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    device.backing.deviceName = profile.get('vlan', '')
                    network_spec.device = device
                    spec.deviceChange.append(network_spec)
                    break
    
            # Reconfigure the VM with the updated specifications
            task = vm.ReconfigVM_Task(spec)
            print("Modifying VM...")
            self.wait_for_task(task)
            print("VM '{}' modified successfully.".format(vm_name))
    
        except Exception as e:
            print("Error modifying VM:", str(e))

def get_vm_by_name(vm_name, content):
    vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view
    for vm in vm_list:
        if vm.name == vm_name:
            return vm
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VMware VM Provisioning Tool")
    parser.add_argument("vm", help="Specify 'vm' to indicate VM-related commands")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: create
    create_parser = subparsers.add_parser("create", help="Create a VM from the template specified in the profile file")
    create_parser.add_argument("profile_name", help="Name of the profile to create VM")

    # Subcommand: delete
    delete_parser = subparsers.add_parser("delete", help="Delete VM irreversibly")
    delete_parser.add_argument("vm_name", help="Name of the VM to delete")

    # Subcommand: list
    subparsers.add_parser("list", help="List VMs in table view with basic info")

    # Subcommand: snapshot
    snapshot_parser = subparsers.add_parser("snapshot", help="Take snapshot of the specified VM")
    snapshot_parser.add_argument("vm_name", help="Name of the VM to create a snapshot")

    # Subcommand: modify
    modify_parser = subparsers.add_parser("modify", help="Modify an existing VM based on the specified profile")
    modify_parser.add_argument("vm_name", help="Name of the existing VM to modify")
    modify_parser.add_argument("profile_name", help="Name of the profile containing the desired configurations")

    args = parser.parse_args()

    vcenter_config_file = "vcenter_config.yaml"
    profiles_path = "vm_profiles"

    vcenter_connector = vCenterConnector(vcenter_config_file)
    if vcenter_connector.connect():
        vm_manager = VMManager(vcenter_connector.service_instance, profiles_path)
        vm_manager.load_profiles()

        if args.vm == "vm":
            if args.command == "create":
                vm_manager.create_vm(args.profile_name)
            elif args.command == "delete":
                vm_manager.delete_vm(args.vm_name)
            elif args.command == "list":
                vm_manager.list_vms()
            elif args.command == "snapshot":
                vm_manager.create_snapshot(args.vm_name)
            elif args.command == "modify":
                vm_manager.modify_vm(args.vm_name, args.profile_name)
            else:
                parser.print_help()
        else:
            print("Invalid command. Please use 'vm' as the parameter.")

        vcenter_connector.disconnect()
    else:
        print("Failed to connect to vCenter")
