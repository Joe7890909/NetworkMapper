import pandas as pd
import socket
import concurrent.futures
from concurrent.futures import as_completed
import time
from netmiko import SSHDetect, ConnectHandler
from netaddr import IPNetwork
def iplistcreater(ipaddress, subnetmask):
    ip_addr = ipaddress
    mask = subnetmask
    network = IPNetwork('/'.join([ip_addr, mask]))
    generator = network.iter_hosts()
    return list(generator)

def detect_device_helper(username, password, ip): 
    command = "show run" 
    result = {} 
    # Define device parameters 
    device = { 'device_type': "autodetect", 
          # Change this accordingly if not using Cisco IOS 
          'ip': ip, 
          'username': username, 
          'password': password, } 
    try: 
        guesser = SSHDetect(**device) 
        best_match = guesser.autodetect() 
        print(best_match) 
        # Name of the best device_type to use further 
        print(guesser.potential_matches) 
        # Dictionary of the whole matching result 
        # Update the 'device' dictionary with the device_type 
        device["device_type"] = best_match 
        # Establish an SSH connection to the device 
        net_connect = ConnectHandler(**device) 
        print(net_connect.find_prompt()) 
        # Execute the show run command 
        output = net_connect.send_command(command) 
        # Store the command output 
        result[ip] = output 
        # Close the connection 
        net_connect.disconnect() 
    except Exception as e: print(f"Failed to connect to {ip}: {e}") 
    result[ip] = None 
    return result 
def detect_device(username, password, ip_addresses): 
    results = {} 
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ip_addresses)) as executor: 
            # Creating a list of tasks 
        future_to_ip = {executor.submit(detect_device_helper, username, password, ip): ip for ip in ip_addresses} 
        # As each task completes, get the result and update the main results dictionary 
        for future in as_completed(future_to_ip): ip = future_to_ip[future] 
        try: 
            result = future.result() 
            results.update(result) 
        except Exception as exc: 
            print(f'{ip} generated an exception: {exc}') 
        results[ip] = None 
        return results

# Function to ping an IP address by trying to connect to port 22 (SSH)
def ping_ip(address):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        port = 22
        try:
            
            s.settimeout(1)  # Set timeout to 1 second
            s.connect((address, port))
            return f"Success: {address}"
        except socket.error:  # Catch socket-related errors
            s.close()
            return f"Failed: {address}"
            

# Function to read an Excel file and extract IP addresses
def readxfile(filepath):
    # Load the Excel file
    df = pd.read_excel(filepath)

    # Check if "IP Address" column exists
    if "IP Address" not in df.columns:
        print("Column 'IP Address' not found.")
        return []

    # Extract IP addresses into a list
    ip_addresses = df["IP Address"].dropna().tolist()
    return ip_addresses

# Function to ping a list of IP addresses concurrently
def pingmadd(iplist):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(ping_ip, iplist))
        return results

def searchlist(iplist):
    Slist = []
    for i in iplist:
        if i.startswith("S"):
            Slist.append(i)
            print(Slist)
    for x in Slist:
        Slist = Slist.append(x[9:])
        print(Slist)
    return Slist
def mainmenu():
    userinput = input("excel or IP: ")
    if userinput == "excel":
        ipaddress = input("Input Excel File Path: ")
    elif userinput == "IP":
        ipaddress = input("Input Network IP Address: ")
        print(ipaddress)
    return ipaddress


    

    

def main():
    start = time.time()
    useroption = mainmenu()
    decide = useroption[1]
    if decide[0].isdigit() == True:
        useroption = useroption.split()
        ipaddress = useroption[0]
        subnetmask = useroption[1]
        ipaddresslist = iplistcreater(ipaddress, subnetmask)
    else:
        ipaddresslist = readxfile(useroption)
    iplist = pingmadd(ipaddresslist)
    newlist = searchlist(iplist)
    #detect_device("", "",newlist)
    with open ("C:/SerialPing/ping.txt", "w") as f:
        for i in iplist:
            f.write(f"{i}\n")
    end = time.time()
    print(end - start)
    

if __name__ == "__main__":
    main()