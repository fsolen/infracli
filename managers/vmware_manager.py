import os
import yaml
import logging
import time
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from .phpipam_manager import PhpIpamManager
from .vault_manager import VaultManager

class VMManager:
    def __init__(self, site_config, profiles_path):
        self.site_config = site_config
        self.vault_manager = VaultManager(site_config)
        self.credentials = self.vault_manager.read_secret(self.site_config['vault_path'])
        self.service_instance = self.connect_to_vcenter()
        self.profiles_path = profiles_path
        self.profiles = self.load_profiles()
        self.phpipam_manager = PhpIpamManager(site_config)
        self.logger = logging.getLogger(__name__)

    def connect_to_vcenter(self):
        host = self.site_config['vcenter']['host']
        username = self.credentials['username']
        password = self.credentials['password']
        context = None
        if hasattr(ssl, "_create_unverified_context"):
            context = ssl._create_unverified_context()
        try:
            return SmartConnect(host=host, user=username, pwd=password, sslContext=context)
        except Exception as e:
            self.logger.error(f"Unable to connect to vCenter: {str(e)}")
            return None

    def disconnect(self):
        try:
            if self.service_instance:
                Disconnect(self.service_instance)
                self.logger.info("Disconnected from vCenter")
        except Exception as e:
            self.logger.error(f"Error disconnecting from vCenter: {str(e)}")

    def load_profiles(self):
        profiles = {}
        for filename in os.listdir(self.profiles_path):
            if filename.endswith(".yaml"):
                try:
                    with open(os.path.join(self.profiles_path, filename), 'r') as f:
                        profile = yaml.safe_load(f)
                        profile_name = os.path.splitext(filename)[0]
                        profiles[profile_name] = profile
                        self.logger.info(f"Loaded profile {profile_name}")
                except Exception as e:
                    self.logger.error(f"Error loading profile {filename}: {str(e)}")
        return profiles

    def select_host(self):
        try:
            content = self.service_instance.RetrieveContent()
            hosts = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view
            selected_host = None
            min_cpu_usage = float('inf')
            min_memory_usage = float('inf')

            for host in hosts:
                host_summary = host.summary
                if host_summary.runtime.connectionState == "connected":
                    cpu_usage = host_summary.quickStats.overallCpuUsage
                    memory_usage = host_summary.quickStats.overallMemoryUsage
                    if cpu_usage < min_cpu_usage and memory_usage < min_memory_usage:
                        min_cpu_usage = cpu_usage
                        min_memory_usage = memory_usage
                        selected_host = host

            if selected_host:
                self.logger.info(f"Selected host: {selected_host.name}")
            else:
                self.logger.warning("No suitable host found")

            return selected_host
        except Exception as e:
            self.logger.error(f"Failed to select host: {str(e)}")
            return None

    def select_datastore(self, host, profile):
        try:
            selected_datastore = None
            max_remaining_capacity = 0

            # Calculate total disk size from the profile
            total_disk_size = sum(disk['size_gb'] * 1024**3 for disk in profile['disks'])  # Convert GB to bytes

            for datastore in host.datastore:
                summary = datastore.summary
                if summary.multipleHostAccess:  # Filter shared datastores
                    total_capacity = summary.capacity
                    usable_capacity = total_capacity * 0.8  # Use 80% of total capacity to leave room for overhead
                    remaining_capacity = usable_capacity - total_disk_size

                    if remaining_capacity > max_remaining_capacity:
                        max_remaining_capacity = remaining_capacity
                        selected_datastore = datastore

            if selected_datastore:
                self.logger.info(f"Selected datastore: {selected_datastore.name}")
            else:
                self.logger.warning("No suitable datastore found")

            return selected_datastore
        except Exception as e:
            self.logger.error(f"Failed to select datastore: {str(e)}")
            return None

    def create_vm(self, site, profile):
        try:
            content = self.service_instance.RetrieveContent()
            datacenter = content.rootFolder.childEntity[0]
            vm_folder = datacenter.vmFolder
            resource_pool = datacenter.hostFolder.childEntity[0].resourcePool

            # Select host and datastore
            host = self.select_host()
            if not host:
                self.logger.error("No suitable host found for VM deployment")
                return

            datastore = self.select_datastore(host, profile)
            if not datastore:
                self.logger.error("No suitable datastore found for VM deployment")
                return

            # Create VM configuration
            vm_name = profile['hostname_pattern'].format(index=1)
            vm_config = vim.vm.ConfigSpec(
                name=vm_name,
                memoryMB=profile['memory'],
                numCPUs=profile['cpu'],
                guestId='otherGuest',
                version='vmx-19'  # Latest virtual hardware version for vSphere 8
            )

            # Add disks
            for i, disk in enumerate(profile['disks']):
                disk_spec = vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
                    device=vim.vm.device.VirtualDisk(
                        backing=vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                            fileName=f"[{datastore.name}] {vm_name}/{disk['name']}.vmdk",
                            diskMode='persistent'
                        ),
                        capacityInKB=disk['size_gb'] * 1024 * 1024,
                        key=-1,
                        unitNumber=i,
                        controllerKey=1000
                    )
                )
                vm_config.deviceChange.append(disk_spec)

            # Add network interfaces
            for i, network in enumerate(profile['networks']):
                nic_spec = vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
                    device=vim.vm.device.VirtualVmxnet3(
                        backing=vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                            deviceName=network['name']
                        ),
                        key=-1,
                        unitNumber=i,
                        controllerKey=100
                    )
                )
                vm_config.deviceChange.append(nic_spec)

            # Clone the VM from the template
            template_vm = self.get_vm_by_name(profile['template_name'], content)
            if not template_vm:
                self.logger.error(f"Template {profile['template_name']} not found")
                return

            clone_spec = vim.vm.CloneSpec(
                location=vim.vm.RelocateSpec(
                    datastore=datastore,
                    host=host,
                    pool=resource_pool
                ),
                powerOn=False,
                template=False
            )

            task = template_vm.Clone(folder=vm_folder, name=vm_name, spec=clone_spec)
            self.logger.info("Cloning VM from template...")

            self.wait_for_task(task, "VM creation")

        except Exception as e:
            self.logger.error(f"Failed to create VM: {str(e)}")

    def delete_vm(self, vm_name):
        try:
            content = self.service_instance.RetrieveContent()
            vm = self.get_vm_by_name(vm_name, content)
            if not vm:
                self.logger.error(f"VM {vm_name} not found")
                return

            task = vm.Destroy_Task()
            self.logger.info(f"Deleting VM {vm_name}...")

            self.wait_for_task(task, "VM deletion")

        except vim.fault.InvalidLogin as e:
            self.logger.error(f"Invalid login credentials: {e}")
        except vim.fault.NoPermission as e:
            self.logger.error(f"No permission to access vCenter: {e}")
        except Exception as e:
            self.logger.error(f"Failed to delete VM: {e}")

    def list_vms(self):
        try:
            content = self.service_instance.RetrieveContent()
            vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view
            vms = []
            for vm in vm_list:
                summary = vm.summary
                vms.append([
                    summary.config.name,
                    summary.config.numCpu,
                    summary.config.memorySizeMB,
                    summary.storage.committed / (1024**3),  # Convert bytes to GB
                    len(self.get_all_snapshots_names(vm.snapshot.rootSnapshotList)) if vm.snapshot else 0
                ])
            return vms

        except vim.fault.InvalidLogin as e:
            self.logger.error(f"Invalid login credentials: {e}")
            return []
        except vim.fault.NoPermission as e:
            self.logger.error(f"No permission to access vCenter: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Failed to list VMs: {e}")
            return []

    def create_snapshot(self, vm_name):
        try:
            content = self.service_instance.RetrieveContent()
            vm = self.get_vm_by_name(vm_name, content)
            if not vm:
                self.logger.error(f"VM {vm_name} not found")
                return

            task = vm.CreateSnapshot_Task(name=f"{vm_name}-snapshot", description="Snapshot created by script", memory=False, quiesce=False)
            self.logger.info(f"Creating snapshot for VM {vm_name}...")

            self.wait_for_task(task, "Snapshot creation")

        except vim.fault.InvalidLogin as e:
            self.logger.error(f"Invalid login credentials: {e}")
        except vim.fault.NoPermission as e:
            self.logger.error(f"No permission to access vCenter: {e}")
        except Exception as e:
            self.logger.error(f"Failed to create snapshot: {e}")

    def modify_vm(self, vm_name, profile):
        try:
            content = self.service_instance.RetrieveContent()
            vm = self.get_vm_by_name(vm_name, content)
            if not vm:
                self.logger.error(f"VM {vm_name} not found")
                return

            vm_config = vim.vm.ConfigSpec(
                memoryMB=profile['memory'],
                numCPUs=profile['cpu']
            )

            # Modify disks
            for i, disk in enumerate(profile['disks']):
                disk_spec = vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
                    device=vim.vm.device.VirtualDisk(
                        capacityInKB=disk['size_gb'] * 1024 * 1024,
                        key=-1,
                        unitNumber=i,
                        controllerKey=1000
                    )
                )
                vm_config.deviceChange.append(disk_spec)

            # Modify network interfaces
            for i, network in enumerate(profile['networks']):
                nic_spec = vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.edit,
                    device=vim.vm.device.VirtualVmxnet3(
                        backing=vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                            deviceName=network['name']
                        ),
                        key=-1,
                        unitNumber=i,
                        controllerKey=100
                    )
                )
                vm_config.deviceChange.append(nic_spec)

            task = vm.ReconfigVM_Task(spec=vm_config)
            self.logger.info(f"Modifying VM {vm_name} with profile {profile['hostname_pattern']}...")

            self.wait_for_task(task, "VM modification")

        except vim.fault.InvalidLogin as e:
            self.logger.error(f"Invalid login credentials: {e}")
        except vim.fault.NoPermission as e:
            self.logger.error(f"No permission to access vCenter: {e}")
        except Exception as e:
            self.logger.error(f"Failed to modify VM: {e}")

    def get_vm_by_name(self, vm_name, content):
        try:
            vm_list = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True).view
            for vm in vm_list:
                if vm.name == vm_name:
                    return vm
        except Exception as e:
            self.logger.error(f"Error retrieving VM by name: {str(e)}")
        return None

    def wait_for_task(self, task, action_name):
        timeout = 600  # Timeout in seconds
        start_time = time.time()

        while task.info.state == vim.TaskInfo.State.running:
            if time.time() - start_time > timeout:
                self.logger.error(f"Error: {action_name} task timed out")
                return
            time.sleep(5)  # Sleep for 5 seconds before checking again

        if task.info.state == vim.TaskInfo.State.success:
            self.logger.info(f"{action_name} completed successfully")
        else:
            self.logger.error(f"Error during {action_name}: {task.info.error}")
