import argparse
import concurrent.futures
import time
from typing import List, Dict

from netmiko import ConnectHandler, SSHDetect
from netaddr import IPNetwork


def ip_range(ip: str, mask: str) -> List[str]:
    network = IPNetwork(f"{ip}/{mask}")
    return [str(host) for host in network.iter_hosts()]


def connect_and_run(ip: str, username: str, password: str, commands: List[str]) -> Dict[str, str]:
    device = {
        "device_type": "autodetect",
        "ip": ip,
        "username": username,
        "password": password,
    }
    try:
        guesser = SSHDetect(**device)
        best_type = guesser.autodetect()
        device["device_type"] = best_type
        conn = ConnectHandler(**device)
    except Exception:
        # fallback to telnet (assumes Cisco IOS-style)
        device["device_type"] = "cisco_ios_telnet"
        try:
            conn = ConnectHandler(**device)
        except Exception as err:
            return {ip: f"Connection failed: {err}"}
    output = []
    for cmd in commands:
        try:
            output.append(conn.send_command(cmd))
        except Exception as e:
            output.append(f"Failed to run {cmd}: {e}")
    conn.disconnect()
    return {ip: "\n".join(output)}


def scan_subnet(ip: str, mask: str, username: str, password: str, commands: List[str]) -> Dict[str, str]:
    hosts = ip_range(ip, mask)
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        future_to_ip = {ex.submit(connect_and_run, host, username, password, commands): host for host in hosts}
        for future in concurrent.futures.as_completed(future_to_ip):
            host = future_to_ip[future]
            try:
                results.update(future.result())
            except Exception as exc:
                results[host] = f"Error: {exc}"
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple network mapper using Netmiko")
    parser.add_argument("ip", help="Network IP address")
    parser.add_argument("mask", help="Subnet mask")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("commands", nargs='+', help="Commands to execute on each device")
    args = parser.parse_args()

    start = time.time()
    result = scan_subnet(args.ip, args.mask, args.username, args.password, args.commands)
    for host, output in result.items():
        print(f"\n===== {host} =====\n{output}\n")
    print(f"Completed in {time.time() - start:.2f}s")


if __name__ == "__main__":
    main()
