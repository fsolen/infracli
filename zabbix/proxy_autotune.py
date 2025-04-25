#!/usr/bin/env python3

import json
import subprocess
import datetime
from pathlib import Path

def log(msg, log_file):
    with open(log_file, "a") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")

def get_busy(proc, host):
    try:
        cmd = f"zabbix_get -s {host} -k 'zabbix[process,{proc},avg,busy]'"
        return float(subprocess.check_output(cmd, shell=True).decode().strip())
    except Exception as e:
        return 0.0

def get_current_memory_mb():
    with open('/proc/meminfo') as f:
        lines = f.readlines()
    mem_free = sum(int(line.split()[1]) for line in lines if 'MemFree' in line or 'Buffers' in line or 'Cached' in line)
    return mem_free // 1024

def get_used_memory_mb():
    with open('/proc/meminfo') as f:
        lines = f.readlines()
    total = int(next(l for l in lines if l.startswith("MemTotal")).split()[1])
    free = sum(int(line.split()[1]) for line in lines if 'MemFree' in line or 'Buffers' in line or 'Cached' in line)
    return (total - free) // 1024

def parse_config(path):
    data = {}
    with open(path, "r") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                k, v = k.strip(), v.strip()
                if v.endswith("M"):
                    v = v[:-1]
                if v.isdigit():
                    data[k] = int(v)
    return data

def update_config(config_file, param, new_value):
    lines = []
    updated = False
    param_line = f"{param}="
    with open(config_file, "r") as f:
        for line in f:
            if line.startswith(param_line):
                lines.append(f"{param}={new_value}M\n" if "Cache" in param else f"{param}={new_value}\n")
                updated = True
            else:
                lines.append(line)
    if updated:
        backup_path = config_file + ".bak"
        Path(backup_path).write_text("".join(lines))
        with open(config_file, "w") as f:
            f.writelines(lines)
    return updated

def update_memory_parameters(config_path, memory_params, current_config, log_file, total_ram_mb):
    updated = False
    used = get_used_memory_mb()
    used_percent = (used / total_ram_mb) * 100

    if used_percent > 85:
        log(f"Skipping memory param updates. Used RAM is {used_percent:.1f}% (>85%)", log_file)
        return False

    for key, val in memory_params.items():
        current_val = current_config.get(key, 0)
        new_val = current_val + val["step"]
        if new_val <= val["max"]:
            update_config(config_path, key, new_val)
            log(f"{key} increased from {current_val}M to {new_val}M due to RAM availability ({100-used_percent:.1f}% free)", log_file)
            updated = True
        else:
            log(f"{key} not updated: would exceed max of {val['max']}M", log_file)

    return updated

def main():
    with open("/etc/zabbix/zabbix_tune_config.json") as f:
        cfg = json.load(f)

    config_path = cfg["config_path"]
    threshold = cfg["threshold"]
    zabbix_host = cfg["zabbix_get_host"]
    log_file = cfg["log_file"]
    restart_command = cfg["restart_command"]
    max_total_memory = cfg["max_total_memory_mb"]
    parameters = cfg["parameters"]
    memory_params = cfg.get("memory_parameters", {})

    current_values = parse_config(config_path)
    mem_free = get_current_memory_mb()
    total_allocated = sum(current_values.get(p["config_key"], 0) for p in parameters.values())

    changed = False

    for process_type, details in parameters.items():
        current_busy = get_busy(process_type, zabbix_host)
        config_key = details["config_key"]
        step = details["step"]
        max_value = details["max"]

        if current_busy > threshold:
            current = current_values.get(config_key, 0)
            if current + step <= max_value:
                if total_allocated + step <= max_total_memory:
                    updated = update_config(config_path, config_key, current + step)
                    if updated:
                        log(f"{config_key} increased from {current} to {current + step} due to {process_type} busy={current_busy:.1f}%", log_file)
                        changed = True
                        total_allocated += step
                else:
                    log(f"Skipped tuning {config_key}: memory limit exceeded.", log_file)
            else:
                log(f"Skipped tuning {config_key}: max value reached.", log_file)

    changed |= update_memory_parameters(config_path, memory_params, current_values, log_file, max_total_memory)

    if changed:
        subprocess.run(restart_command.split())
        log("Zabbix Proxy restarted due to config update.", log_file)

if __name__ == "__main__":
    main()
