from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import os
import yaml

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
      
  def modify_network_adapters(self, vm, profile):
      # Get the network settings from the profile
      net_settings = profile.get('net', [])
  
      # Get the network adapters from the VM
      network_adapters = [device for device in vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualEthernetCard)]
  
      # Iterate over the network settings
      for i, net_setting in enumerate(net_settings):
          # Check if the network adapter already exists
          if i < len(network_adapters):
              # Check if the existing network adapter is not VMXNET3
              if not isinstance(network_adapters[i], vim.vm.device.VirtualVmxnet3):
                  # Remove the existing network adapter
                  device_change = vim.vm.device.VirtualDeviceSpec()
                  device_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
                  device_change.device = network_adapters[i]
                  vm.config.hardware.device.append(device_change)
  
                  # Add a new VMXNET3 network adapter
                  new_network_adapter = vim.vm.device.VirtualVmxnet3()
                  new_network_adapter.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                  new_network_adapter.backing.deviceName = net_setting
                  new_network_adapter.addressType = 'assigned'
                  new_network_adapter.key = -1
                  new_network_adapter.deviceInfo.summary = 'VMXNET3'
  
                  # Add the new network adapter to the VM configuration
                  device_change = vim.vm.device.VirtualDeviceSpec()
                  device_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                  device_change.device = new_network_adapter
                  vm.config.hardware.device.append(device_change)
              else:
                  # Update the existing VMXNET3 network adapter
                  network_adapters[i].backing.deviceName = net_setting
          else:
              # Add a new VMXNET3 network adapter
              new_network_adapter = vim.vm.device.VirtualVmxnet3()
              new_network_adapter.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
              new_network_adapter.backing.deviceName = net_setting
              new_network_adapter.addressType = 'assigned'
              new_network_adapter.key = -1
              new_network_adapter.deviceInfo.summary = 'VMXNET3'
  
              # Add the new network adapter to the VM configuration
              device_change = vim.vm.device.VirtualDeviceSpec()
              device_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
              device_change.device = new_network_adapter
              vm.config.hardware.device.append(device_change)
                          
  def modify_disks(self, vm, profile):
      # Get the disk configurations from the profile
      disk_configs = profile.get('disks', [])
  
      # Get the disks from the VM
      disks = [device for device in vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualDisk)]
  
      # Iterate over the disk configurations
      for disk_config in disk_configs:
          # Check if the disk configuration exists in the VM
          disk_found = False
          for disk in disks:
              if disk.deviceInfo.label == disk_config.get('name'):
                  disk_found = True
                  break
  
          # If the disk configuration is not found, add it to the VM
          if not disk_found:
              print("You specified in the profile '{}', but the VM does not have a disk named '{}'.".format(disk_config.get('name'), disk_config.get('name')))
              print("Adding disk '{}' with size {} GB to the VM.".format(disk_config.get('name'), disk_config.get('size_gb')))
  
  
              # Create a new disk device
              new_disk = vim.vm.device.VirtualDisk()
              new_disk.key = -1
              new_disk.controllerKey = 0
              new_disk.unitNumber = len(vm.config.hardware.device)
              new_disk.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
              new_disk.backing.diskMode = 'persistent'
              new_disk.backing.fileName = ''
              new_disk.capacityInKB = disk_config.get('size_gb') * 1024 * 1024
  
              # Add the new disk to the VM configuration
              device_change = vim.vm.device.VirtualDeviceSpec()
              device_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
              device_change.device = new_disk
              vm.config.hardware.device.append(device_change)
  
          # If the disk configuration exists in the VM, update it
          else:
              # Find the disk in the VM configuration
              for disk in vm.config.hardware.device:
                  if isinstance(disk, vim.vm.device.VirtualDisk) and disk.deviceInfo.label == disk_config.get('name'):
                      # Update the disk configuration
                      disk.capacityInKB = disk_config.get('size_gb') * 1024 * 1024
  
                      # Create a device change specification
                      device_change = vim.vm.device.VirtualDeviceSpec()
                      device_change.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                      device_change.device = disk
  
                      # Add the device change to the VM configuration
                      vm.config.spec.deviceChange.append(device_change)

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
            self.modify_disks(vm, profile)
   
            # Change network port group (VLAN)
            self.modify_network_adapters(vm, profile)
    
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
