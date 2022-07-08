#######################
# IMPORTING LIBRARIES #
#######################

import socket
import atexit
import sys
import threading
import time
from colorama import Fore, Style, Back, init as colorama_init
from rich.console import Console
import os
import getpass
from hashlib import sha256
import json
from utils import *
from functools import wraps

##################
# COLORAMA STUFF #
##################
colorama_init()


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
            # style_table_print(f"{Fore.RED}[ ERROR ] Error encountered while connecting: {e}")
            return False
        else:
            # print(f"{Fore.GREEN}[ SUCCESS ] Successfully connected to {Fore.YELLOW}{self.SERVER_IP}{Fore.GREEN}:{Fore.YELLOW}{self.SERVER_PORT}{Fore.GREEN}!")
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
        style_table_print(f"Sending starting info...", start=False)

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

                self.send_data(message_json, echo=False)

                # print(f"{Fore.CYAN}-+= SENDING =+-\n--++==>> {message_json}")

                # Waiting a little
                time.sleep(0.2)

                # Receiving
                try:
                    data_received = self.recv_data(echo=False)
                    # info_print(data_received)

                    data_received = json.loads(data_received)
                    # print(f"RECEIVED: {data_received}")
                except Exception as e:
                    # print(f"Unable to convert received data to dict -> {e}")
                    style_table_print(f"ERROR", start=False)
                    data_received = {"verified": "ERROR"}

                style_table_print("Authenticating...", start=False)
                if self.login_method == "login":
                    self.verified = data_received['verified']

                    if not self.verified:
                        clear()
                        style_table_print(f"Credentials are wrong!", start=False)
                        self.username = input(f"{Fore.CYAN}| {Fore.YELLOW}Username:{Fore.MAGENTA} ")
                        self.password = getpass.getpass(f"{Fore.CYAN}| {Fore.YELLOW}Password: ", stream=None)
                elif self.login_method == "register":
                    self.verified = data_received['created']
                elif self.login_method == "guest":
                    self.verified = data_received['allowed']

            style_table_print(f"Your client has been verified!", start=False)
        except socket.error as e:
            style_table_print(f"AN ERROR OCCURRED!", start=False)
            # print(f"{Fore.RED}[ ERROR ] Unable to handle starting communications -> {e}")
            return False

        # time.sleep(10)

        # print(f"{Fore.GREEN}[ SUCCESS ] Starting communications were successful!")
        return True

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

    def send_data(self, data: str, echo=True) -> bool:
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

            if echo:
                print(f"{Fore.CYAN}[ SENT ] - {data}")
            log(data, "client", "sent", echo=False)

            return True
        except socket.error as e:
            print(f"{Fore.RED}[ ERROR ] Unable to send data -> {e}")
            return False

    def recv_data(self, echo=True) -> str:
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

        if echo:
            print(f"{Fore.MAGENTA}[ RECEIVED ] - {res[self.HEADER_SIZE:]}")
        log(res[self.HEADER_SIZE:], "client", "received", echo=False)

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

client_auth_option = ""

username = str()
password = str()

version = "0.1b"

stop_threads = False

messages_buffer = []
stop_input_buffer_adding = False


#####################
# UTILITY FUNCTIONS #
#####################
def clear():
    try:
        os.system("clear")
    except:
        os.system("cls")


def on_exit():
    # clear()

    style_table_print("Exiting...")

    style_table_print("Closing threads...", start=False)

    global stop_threads
    stop_threads = True

    # style_table_print("Threads closed!", start=False)

    style_table_print("Closing socket...", start=False)

    client.close()

    # style_table_print("Socket closed!", start=False)

    style_table_print("GOOD BYE <3", start=False)

    sys.exit()


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

    num_of_symbols = max_amount_of_symbols - int(text_len / 2)

    if text_len < num_of_symbols:
        res = symbol * num_of_symbols + f" {text} " + symbol * num_of_symbols
    else:
        res = symbol * num_of_symbols + f"{text}" + symbol * num_of_symbols

    print(res)


def style_table_print(text, max_len=20, start=True, end=True):
    max_len = len("-----------------------------------")

    len_of_text = len(text)
    len_of_spaces = int((max_len - len_of_text + 1))

    final_text = f"{Fore.CYAN}|{Fore.YELLOW} {text} {' ' * (len_of_spaces - 2)}{Fore.CYAN}|"

    if len(final_text) > 52:
        final_text = final_text[:46]
        final_text += f"{Fore.CYAN}|"

    sep = f"{Fore.CYAN}|{'-' * (int(max_len))}|"

    if start:
        print(sep)
    print(final_text)
    if end:
        print(sep)


def ask_exit_script():
    successful = False

    while not successful:
        user_in = input(f"{Fore.YELLOW}Are you sure? [Y/N]\n> {Fore.MAGENTA}")

        if user_in.lower() == "y":
            clear()
            successful = True
            on_exit()
        elif user_in.lower() == "n":
            print(f"{Fore.GREEN}:D")
            time.sleep(0.4)
            clear()
            successful = True
        else:
            print(f"{Fore.RED}Please answer correctly!")
            time.sleep(0.6)


#############
# FUNCTIONS #
#############
def handle_sending_msgs():
    # Global variables
    global stop_input_buffer_adding

    # Other
    while not stop_threads:
        # 1
        # messages_buffer.append("INPUT")
        # stop_input_buffer_adding = False
        # input_buffer_thread = threading.Thread(target=add_input_to_buffer)
        # input_buffer_thread.start()
        #
        # user_msg = input('')
        #
        # stop_input_buffer_adding = True
        #
        # client.send_data(user_msg, echo=False)

        # 2
        messages_buffer.append("INPUT")
        stop_input_buffer_adding = False
        input_buffer_thread = threading.Thread(target=add_input_to_buffer)
        input_buffer_thread.start()

        user_msg = input(f"{Fore.CYAN}| {Fore.BLUE}You{Fore.CYAN}:{Fore.MAGENTA} ")

        stop_input_buffer_adding = True

        client.send_data(user_msg, echo=False)


def add_input_to_buffer():
    global messages_buffer

    if len(messages_buffer) >= 10:
        messages_buffer = ["INPUT"]

    while not stop_input_buffer_adding:
        messages_buffer[-1] = "INPUT"


def handle_receiving_msgs():
    connected = True

    while not stop_threads and connected:
        data_received = client.recv_data(echo=False)

        if not client.username in data_received.split(":")[0]:
            if messages_buffer[-1] == "INPUT":
                print(f"\n{Fore.CYAN}| {Style.RESET_ALL}{data_received}\n{Fore.CYAN}| {Fore.CYAN}You: {Fore.MAGENTA}", end='')
            else:
                print(f"{Fore.CYAN}| {Style.RESET_ALL}{data_received}{Fore.MAGENTA}")
                messages_buffer.append(data_received)


def get_username_pass(login_method: str):
    # GLOBAL VARIABLES
    global username
    global password

    proceed = False

    while not proceed:
        try:
            style_table_print("CREDENTIALS")

            if login_method.lower() == "login" or login_method.lower() == "1":
                username = input(f"{Fore.CYAN}| {Fore.YELLOW}Username: {Fore.MAGENTA}")
                password = getpass.getpass(f"{Fore.CYAN}| {Fore.YELLOW}Password: ", stream=False)
                proceed = True
            elif login_method.lower() == "register" or login_method.lower() == "2":
                username = input(f"{Fore.CYAN}| {Fore.YELLOW}Username:{Fore.MAGENTA} ")
                password = getpass.getpass(f"{Fore.CYAN}| {Fore.YELLOW}New Password: ", stream=False)
                confirm = getpass.getpass(f"{Fore.CYAN}| {Fore.YELLOW}Confirm Password: ", stream=False)

                if password == confirm:
                    proceed = True
                else:
                    print(
                        f"{Fore.CYAN}| {Fore.RED}Please retype your credentials.\n{Fore.CYAN}|{Fore.RED} Unable to register account!")
                    time.sleep(1)
                    clear()
            elif login_method.lower() == "guest" or login_method.lower() == "3":
                username = input(f"{Fore.CYAN}| {Fore.YELLOW}Username: {Fore.MAGENTA}")
                password = "guest"
                proceed = True
        except KeyboardInterrupt as e:
            print("\n", end="\r")
            ask_exit_script()

    client.username = username
    client.password = password

    clear()
    print(Style.RESET_ALL)
    clear()


def register_or_login_menu():
    clear()

    proceed = False

    while not proceed:
        style_table_print("AUTHENTICATION OPTIONS")
        style_table_print(f"1. ACCOUNT", start=False)
        style_table_print(f"2. REGISTER", start=False)
        style_table_print(f"3. GUEST", start=False)
        style_table_print(f"4. EXIT", start=False)

        try:
            option = input(f"{Fore.CYAN}| {Fore.YELLOW}Enter option:{Fore.MAGENTA} ").lower()

            if option == "1" or option.startswith("a"):
                option = "login"
                proceed = True
            elif option == "2" or option.startswith("reg"):
                option = "register"
                proceed = True
            elif option == "3" or option.startswith("g"):
                option = "guest"
                proceed = True
            elif option == "4" or option.startswith("e"):
                ask_exit_script()
            else:
                print(f"{Fore.CYAN}| {Fore.RED}'{option}' IS AN INVALID OPTION!")
                time.sleep(0.6)
                clear()
        except KeyboardInterrupt as e:
            print("\n", end="\r")
            ask_exit_script()

    print(f"{Style.RESET_ALL}")

    clear()

    get_username_pass(option)

    return option.lower()


def attempt_connection():
    clear()

    is_connected = False

    while not is_connected:
        try:
            style_table_print("SERVER INFORMATION")
            ip = input(f"{Fore.CYAN}| {Fore.YELLOW}Enter IP: {Fore.MAGENTA}")

            try:
                port = int(input(f"{Fore.CYAN}| {Fore.YELLOW}Enter Port: {Fore.MAGENTA}"))
            except ValueError as e:
                print(f"{Fore.CYAN}| {Fore.RED}Please type a number!")
                time.sleep(0.6)
                clear()
                continue

            client.SERVER_IP = ip
            client.SERVER_PORT = port

            is_connected = client.connect_to_server()

            if is_connected:
                break
            else:
                style_table_print("Unable to connect to server!", start=True)
                style_table_print("Make sure the address is correct!", start=False)
                time.sleep(1.5)
                clear()
        except KeyboardInterrupt as e:
            print("\n", end="\r")
            ask_exit_script()

    clear()

    style_table_print("Connection successful!")


def show_credits():
    clear()

    style_table_print("This project was made by MU.")
    input(f"{Fore.CYAN}| {Fore.YELLOW}Press enter to return")

    clear()


def main_menu():
    proceed = False

    # Introductory screen

    while not proceed:
        style_table_print(f"IRC Client v.{version}")
        # style_table_print("", start=False)
        style_table_print(f"OPTIONS", start=False)
        style_table_print(f"1. GO TO MAIN MENU", start=False)
        style_table_print(f"2. CREDITS", start=False)
        style_table_print(f"3. EXIT", start=False)

        try:
            option = input(f"{Fore.CYAN}| {Fore.YELLOW}Enter Option: {Fore.MAGENTA}").lower()

            if option == "1" or option.startswith("g"):
                proceed = True
            elif option == "2" or option.startswith("c"):
                show_credits()
            elif option.startswith("e") or option == "3":
                ask_exit_script()
            else:
                print(f"{Fore.CYAN}| {Fore.RED}'{option}' IS AN INVALID OPTION!")
                time.sleep(1)
                clear()
        except KeyboardInterrupt as e:
            print("\n", end="\r")
            ask_exit_script()


def run():
    # Global variables

    # Displaying main menu
    main_menu()

    # Asking for log in method
    login_option = register_or_login_menu()

    # Attempt connection
    attempt_connection()

    # Setting login method
    client.set_login_method(login_option)
    # print(f"{Fore.YELLOW}Setting login method to {login_option}")

    # Starting communications
    style_table_print("STARTING COMMUNICATIONS")
    style_table_print("Initializing...", start=False, end=False)

    while True:
        if client.starting_communications():
            style_table_print(f"Successfully finished!", start=False)

            try:
                time.sleep(0.6)
            except KeyboardInterrupt as e:
                ask_exit_script()

            break

    clear()

    style_table_print("WELCOME TO THE SERVER!")
    style_table_print(f"Use /help for list of commands!", start=False)

    # Creating data sending thread
    # Receiving is done in this function
    sending_thread = threading.Thread(target=handle_sending_msgs)
    sending_thread.start()

    receiving_thread = threading.Thread(target=handle_receiving_msgs)
    receiving_thread.start()

    return


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
