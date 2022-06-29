#######################
# IMPORTING LIBRARIES #
#######################

import socket
import atexit
import time
from colorama import Fore, Style, Back, init as colorama_init
from rich.console import Console
import os
import getpass
from hashlib import sha256
import json

##################
# COLORAMA STUFF #
##################
colorama_init(autoreset=True)


##########################################
# CLASSES (IF THEY MUST BE IN THIS FILE) #
##########################################
class Client(socket.socket):
    def __init__(self, encoding_format: str, header=10):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)

        # console.log("Initializing Client...")

        self.SERVER_IP = str()
        self.SERVER_PORT = int()
        self.format = encoding_format
        self.HEADER_SIZE = header
        self.verified = False
        self.is_guest = False
        self.login_method = "guest"
        self.username = str()
        self.password = str()

    def connect_to_server(self) -> bool:
        """Attempts to make connection to server.

        Returns:
             bool: Status of connection attempt (successful or not)
        """

        try:
            self.connect((self.SERVER_IP, self.SERVER_PORT))
        except socket.error as e:
            print(f"{Fore.RED}[ ERROR ] Error encountered while connecting: {e}")
            return False
        else:
            print(f"{Fore.GREEN}[ SUCCESS ] Successfully connected to {Fore.YELLOW}{self.SERVER_IP}{Fore.GREEN}:{Fore.YELLOW}{self.SERVER_PORT}{Fore.GREEN}!")
            return True

    def set_login_method(self, option: str) -> bool:
        """Sets login method for the client.

        Parameters:
            option (str): The login option (login, register, guest)

        Returns:
            bool: Login method valid or not
        """
        option = option.lower()

        if option == "login" or option == "guest" or option == "register":
            self.login_method = option
            return True
        else:
            return False

    def starting_communications(self) -> bool:
        """Sends and receives starting data and is used to log in or register.

        Returns:
            bool: If communication was successful or not
        """
        print(f"{Fore.YELLOW}[ INFO ] Sending starting info. Please wait...")

        try:
            while not self.verified:
                # Sending username and password and method of usage
                password_hash = self.hasher(self.password)

                message = {
                    "method": self.login_method,
                    "username": self.username,
                    "password": password_hash
                }

                message_json = json.dumps(message)

                self.send_data(message_json)

                print(f"{Fore.CYAN}-+= SENDING =+-\n--++==>> {message_json}")

                # Waiting a little
                time.sleep(0.2)

                # Receiving
                try:
                    data_received = json.loads(self.recv_data())
                    print(f"RECEIVED: {data_received}")
                except Exception as e:
                    print(f"Unable to convert received data to dict -> {e}")
                    continue
                else:
                    if self.login_method == "login":
                        self.verified = data_received['verified']
                    elif self.login_method == "register":
                        self.verified = data_received['created']
                    elif self.login_method == "guest":
                        self.verified = data_received['allowed']

            print(f"{Fore.GREEN}[ SUCCESS ] Successfully verified client.")
        except socket.error as e:
            print(f"{Fore.RED}[ ERROR ] Unable to handle starting communications -> {e}")
            return False
        else:
            print(f"{Fore.GREEN}[ SUCCESS ] Starting communications were successful!")

    def hasher(self, text: str) -> str:
        """Hashes the given text to a SHA-256 hash

        Parameters:
            text (str): Text to be hashed

        Returns:
            str: Hash
        """
        try:
            hashed_text = sha256(text.encode("utf-8")).hexdigest()
        except Exception as e:
            print(f"{Fore.GREEN}[ ERROR ] Unable to hash the given text -> {e}")
            return

        return hashed_text

    def send_data(self, data: str) -> bool:
        """Sends data to server.

        Parameters:
            data (str): Data to send

        Returns:
            bool: If sending was successful or not
        """
        try:
            data_len = len(data)
        except Exception as e:
            print(f"{Fore.RED}[ ERROR ] Unable to get the length of data to send -> {e}")
            return False

        try:
            data_to_send = f"{data_len:<{self.HEADER_SIZE}}" + data
            data_to_send = data_to_send.encode(self.format)
        except Exception as e:
            print(f"{Fore.RED}[ ERROR ] Unable to encode/format data -> {e}")
            return False

        try:
            self.send(data_to_send)
            return True
        except socket.error as e:
            print(f"{Fore.RED}[ ERROR ] Unable to send data -> {e}")
            return False

    def recv_data(self) -> str:
        """Receives data from server. Uses buffering and streaming!

        Returns:
            str: Received data
        """
        data_received = False
        res = ""
        header_received = False

        while not data_received:
            data = self.recv(4).decode(self.format)

            # console.log(f"Received: {data}\nLength: {len(data)}")

            if not header_received:
                data_len = int(data[:self.HEADER_SIZE])
                # console.log(f"Length of data: {data_len}")
                header_received = True

            res += data

            full_msg_len = len(data)

            # console.log(f"Full message length: {full_msg_len}")

            if len(res) - self.HEADER_SIZE == data_len:
                # console.log("-= FULL DATA RECEIVED =-")
                # console.log(res[self.HEADER_SIZE:])
                data_received = True

        return res[self.HEADER_SIZE:]


#############
# CONSTANTS #
#############
# SERVER_IP = "127.0.1
# SERVER_PORT = 5555

HEADER_SIZE = 10

ENCODING_FORMAT = "ascii"

#############
# VARIABLES #
#############
console = Console()

client = Client(ENCODING_FORMAT)

username = str()
password = str()

version = "0.0.1"


#############
# FUNCTIONS #
#############
def clear():
    try:
        os.system("clear")
    except:
        os.system("cls")


def on_exit():
    clear()

    console.log("Exiting...")

    console.log("Closing socket...")
    client.close()
    console.log("Socket closed!")


def start_screen():
    loading_text("Loading", 0.5)
    
    ascii_print(f"Welcome to IRC Client v.{version}")

    input("Press enter to continue...")
    

def loading_text(text, time_to_sleep: float):
    clear()

    animations = [".", "..", "..."]
    index = 0

    start_time = time.time()

    while True:
        time.sleep(0.1)

        clear()

        elapsed_time = time.time() - start_time
        
        if elapsed_time >= time_to_sleep:
            break

        index += 0.25

        if index >= len(animations):
            index = 0

        current = text + animations[int(index)]

        print(current)

    clear()


def ascii_print(text=None):
    symbol = "="

    max_amount_of_symbols = 20

    if text is None:
        print(symbol * (max_amount_of_symbols * 2 + 1))
        return

    text_len = len(text)

    num_of_symbols = max_amount_of_symbols - int(text_len/2)

    if text_len < num_of_symbols:
        res = symbol * num_of_symbols + f" {text} " + symbol * num_of_symbols
    else:
        res = symbol * num_of_symbols + f"{text}" + symbol * num_of_symbols

    print(res)


def get_username_pass(login_method: str):
    global username
    global password

    ascii_print("CREDENTIALS")
    if login_method.lower() == "login" or login_method.lower() == "1":
        username = input("Username: ")
        password = getpass.getpass("Password: ", stream=False)
    elif login_method.lower() == "register" or login_method.lower() == "2":
        while True:
            username = input("Username: ")
            password = getpass.getpass("New Password: ", stream=False)
            confirm = getpass.getpass("Confirm Password: ", stream=False)

            if password == confirm:
                break
            else:
                print("Please retype your credentials. Unable to register account!")
                time.sleep(1)
                clear()
    elif login_method.lower() == "guest" or login_method.lower() == "3":
        username = input("Username: ")
        password = "guest"

    time.sleep(0.1)

    client.username = username
    client.password = password

    clear()

    loading_text("Loading", 0.5)

    clear()


def register_or_login():
    clear()

    while True:
        ascii_print("IRC")
        ascii_print(f"1. LOGIN")
        ascii_print(f"2. REGISTER")
        ascii_print(f"3. GUEST")
        ascii_print()

        option = input(f"ENTER OPTION ====> ").lower()

        if option == "1" or option == "login":
            option = "login"
            break
        elif option == "2" or option == "register":
            option = "register"
            break
        elif option == "3" or option == "guest":
            option = "guest"
            break
        else:
            clear()
            print(f"[ UNEXPECTED INPUT ] {option} is an invalid option!")

    clear()

    loading_text("Redirecting", 0.5)

    get_username_pass(option)

    return option.lower()


def attempt_connection():
    clear()

    is_connected = False

    while not is_connected:
        ascii_print("ENTER SERVER INFO")
        ip = input("Enter IP: ")
        port = int(input("Enter Port: "))

        client.SERVER_IP = ip
        client.SERVER_PORT = port

        is_connected = client.connect_to_server()

        if is_connected:
            break
        else:
            print("Unable to connect to server. Make sure the address is correct!")
            time.sleep(0.5)
            clear()

    clear()

    print("Connection successful!")


def start_menu():
    start_screen()

    option = register_or_login()

    return option


def run():
    # Global variables

    # Displaying main menu
    option = start_menu()

    # Attempt connection
    attempt_connection()

    # Setting login method
    print(f"{Fore.YELLOW}Setting login method to {option}")

    client.set_login_method(option)

    # Starting communications
    client.starting_communications()

    return

    # Connection

    time.sleep(1)

    clear()

    verified = False

    while not verified:
        print("Use \n   guest => username\n   password => password\nto log in as a guest user!")

        username = input("Username: ")
        password = getpass.getpass("Password: ", stream=None)

        if username.lower() == "guest" and password.lower() == "password":
            client.is_guest = True
            os.system('clear')
            print("Logging in as guest...")
            print("Loading...")
            break

        verified = client.verified

        if verified:
            clear()
            print("You have been verified!")
            print("Loading...")
            break
        else:
            print("Credentials incorrect!")
            time.sleep(1)
            clear()

    time.sleep(1)
    clear()
    # # Creating client socket
    # console.log("Creating client socket...")
    #
    # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #
    # # Connecting to server
    # console.log(f"Connecting to server at {SERVER_IP}:{SERVER_PORT}")
    #
    # client.connect((SERVER_IP, SERVER_PORT))


#########
# OTHER #
#########
if __name__ == "__main__":
    # Clearing the screen
    clear()

    # Registering exiting function
    # atexit.register(on_exit)

    # Running server
    run()
