# Contributing to Infracli

Thank you for considering contributing to the Infracli project! This guide will help you get started with setting up the development environment, understanding the project structure, and contributing code.

## Table of Contents

- [Setting Up the Development Environment](#setting-up-the-development-environment)
- [Project Structure](#project-structure)
- [Configuration Files](#configuration-files)
- [VM Profiles](#vm-profiles)
- [Managers](#managers)
- [Main Script](#main-script)
- [Adding a New Manager](#adding-a-new-manager)
- [Running the CLI Tool](#running-the-cli-tool)
- [Example Commands](#example-commands)
- [Contributing](#contributing)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Setting Up the Development Environment

1. **Clone the Repository**:
   ```sh
   git clone <repository_url>
   cd infracli
   ```

2. **Create a Virtual Environment**:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Project Structure

```
infracli/
├── configs/
│   ├── dnsserver_configs/
│   │   ├── domain1_com.yaml
│   │   ├── domain2_net.yaml
│   │   └── ...
│   ├── hypervisor_configs/
│   │   ├── vmware/
│   │   │   ├── vcenter01_config.yaml
│   │   │   ├── vcenter02_config.yaml
│   │   │   └── ...
│   │   ├── harvester/
│   │   │   ├── harvester01_config.yaml
│   │   │   ├── harvester02_config.yaml
│   │   │   └── ...
│   │   ├── opennebula/
│   │   │   ├── one01_config.yaml
│   │   │   ├── one02_config.yaml
│   │   │   └── ...
│   │   ├── cloudstack/
│   │   │   ├── cloudstack01_configs.yaml
│   │   │   ├── cloudstack02_configs.yaml
│   │   │   └── ...
│   ├── storage_configs/
│   │   ├── purefa01_configs.yaml
│   │   ├── purefa02_configs.yaml
│   │   └── ...
│   └── ...
├── managers/
│   ├── msdns_manager.py
│   ├── vcenter_connector.py
│   ├── vmware_manager.py
│   ├── purestorage_manager.py
│   ├── harvester_manager.py
│   ├── opennebula_manager.py
│   ├── cloudstack_manager.py
│   └── ...
├── vm_profiles/
│   ├── profile1.yaml
│   ├── profile2.yaml
│   └── ...
├── fscli.py
├── requirements.txt
└── ...
```

## Configuration Files

- **Location**: `configs/`
- **Purpose**: Store configurations for different services and environments.
- **Structure**:
  - `dnsserver_configs/`: DNS server configurations.
  - `hypervisor_configs/`: Hypervisor configurations for VMware, Harvester, OpenNebula, and CloudStack.
  - `storage_configs/`: Storage configurations for PureStorage arrays.

## VM Profiles

- **Location**: `vm_profiles/`
- **Purpose**: Define VM configurations and templates.
- **Structure**: YAML files containing VM profiles.

## Managers

- **Location**: `managers/`
- **Purpose**: Contain classes and methods to manage different services.
- **Files**:
  - `msdns_manager.py`: Manages DNS records.
  - `vcenter_connector.py`: Connects to VMware vCenter.
  - `vmware_manager.py`: Manages VMware VMs.
  - `purestorage_manager.py`: Manages PureStorage arrays.
  - `harvester_manager.py`: Manages Harvester VMs.
  - `opennebula_manager.py`: Manages OpenNebula VMs.
  - `cloudstack_manager.py`: Manages CloudStack VMs.

## Main Script

- **Location**: `fscli.py`
- **Purpose**: Entry point for the CLI tool.
- **Functionality**: Parses command-line arguments and invokes appropriate manager methods.

## Adding a New Manager

1. **Create a New Manager File**:
   - Add a new file in the `managers` directory, e.g., `new_manager.py`.

2. **Define the Manager Class**:
   - Implement the necessary methods for managing the new service.

3. **Update `fscli.py`**:
   - Import the new manager class.
   - Add command-line argument parsing for the new manager.

## Running the CLI Tool

1. **Activate the Virtual Environment**:
   ```sh
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. **Run the CLI Tool**:
   ```sh
   python fscli.py <command> <subcommand> [options]
   ```

## Example Commands

- **DNS Management**:
  ```sh
  python fscli.py dns get A example.com domain1.com
  python fscli.py dns add A example.com 192.168.1.1 --ttl 3600 domain1.com
  python fscli.py dns del A example.com 192.168.1.1 domain1.com
  python fscli.py dns list domain1.com
  ```

- **VM Management (VMware)**:
  ```sh
  python fscli.py vm create profile1 vcenter01
  python fscli.py vm delete vm_name vcenter01
  python fscli.py vm list vcenter01
  python fscli.py vm snapshot vm_name vcenter01
  python fscli.py vm modify vm_name profile1 vcenter01
  ```

- **Storage Management**:
  ```sh
  python fscli.py storage create_lun array_name volume_name size
  python fscli.py storage create_host array_name host_name --iqn iqn_value --wwns wwn1 wwn2
  python fscli.py storage add_initiator array_name host_name initiator_name iqn
  python fscli.py storage map_volume array_name volume_name host_name
  python fscli.py storage snapshot_lun array_name volume_name snapshot_name
  python fscli.py storage list_hosts array_name
  python fscli.py storage list_luns array_name
  python fscli.py storage list_host_lun_mappings array_name
  ```

## Contributing

1. **Fork the Repository**:
   - Create a fork of the repository on GitHub.

2. **Create a Feature Branch**:
   ```sh
   git checkout -b feature/new-feature
   ```

3. **Commit Changes**:
   ```sh
   git add .
   git commit -m "Add new feature"
   ```

4. **Push to the Branch**:
   ```sh
   git push origin feature/new-feature
   ```

5. **Create a Pull Request**:
   - Open a pull request on GitHub to merge your changes into the main branch.

## Testing

- **Unit Tests**:
  - Write unit tests for new features and bug fixes.
  - Use a testing framework like `unittest` or `pytest`.

- **Run Tests**:
  ```sh
  pytest tests/
  ```

## Best Practices

- **Code Style**:
  - Follow PEP 8 guidelines for Python code.
  - Use meaningful variable and function names.

- **Error Handling**:
  - Implement proper error handling and logging.
  - Ensure that exceptions are caught and meaningful error messages are displayed.

- **Documentation**:
  - Document your code with comments and docstrings.
  - Update the README file with any new features or changes.

Thank you for contributing to the Infracli project!
