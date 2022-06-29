#######################
# IMPORTING LIBRARIES #
#######################
import os
import socket
import atexit
import json
from colorama import Fore, Back, Style, init as colorama_init
from rich import print
from rich.console import Console
import rich
import threading
from hashlib import sha256

##################
# COLORAMA STUFF #
##################
colorama_init(autoreset=True)

#############
# VARIABLES #
#############
console = Console()

server = None

all_client_data = {}
clients_list = []

#############
# CONSTANTS #
#############
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 5555
SERVER_MAX_CONNECTIONS = 0

MESSAGE_COLON = f"{Fore.CYAN}:{Style.RESET_ALL}"

HEADER_SIZE = 10

ENCODING_FORMAT = "ascii"


##########################################
# CLASSES (IF THEY MUST BE IN THIS FILE) #
##########################################
class Server(socket.socket):
    def __init__(self, encoding_format, max_connections, header_size=10):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)

        console.log("Initializing server...")
        self.SERVER_IP = str()
        self.SERVER_PORT = str()
        self.MAX_CONNECTIONS = max_connections

        self.HEADER_SIZE = header_size

        self.clients = dict()

        self.format = encoding_format

    def send_data(self, data, conn):
        data_len = len(data)

        data_to_send = f"{data_len:<{self.HEADER_SIZE}}" + data
        data_to_send = data_to_send.encode(self.format)

        conn.send(data_to_send)

    def receive_data(self, connection):
        data_received = False
        res = ""
        header_received = False

        while not data_received:
            data = connection.recv(4).decode(self.format)

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

    def get_saved_accounts(self) -> bool:
        try:
            with open("./accounts.hashed") as f:
                read = f.readlines()

                data = []

                for combined in read:
                    combined = combined.strip("\n")
                    account_name = combined.split(":")[0]
                    account_password = combined.split(":")[1]

                    data.append((account_name, account_password))

                data_dict = {
                    "credentials": {}
                }

                for account, password in data:
                    data_dict['credentials'][account] = password

            return data_dict
        except Exception as e:
            print(f"[ ERROR ] Unable to get saved accounts -> {e}")
            return None

    def add_account(self, username, password):
        if not self.verify_account(username, password):
            try:
                with open("./accounts.hashed", "a") as f:
                    f.write(f"\n{username}:{password}")
            except Exception as e:
                print(f"[ ERROR ] Unable to add account -> {e}")

    def verify_account(self, username, password):
        all_accounts = self.get_saved_accounts()
        all_accounts = all_accounts['credentials']
        print(all_accounts)

        try:
            if username in all_accounts:
                if str(all_accounts[username]) == str(password):
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            return False

    def start_server(self):
        console.log(f"Binding server...")

        self.bind((self.SERVER_IP, self.SERVER_PORT))

        console.log(f"Server has been bound!")

        console.log(f"Listening for connections...   [Max: {self.MAX_CONNECTIONS}]")

        self.listen(self.MAX_CONNECTIONS)

        while True:
            conn, addr = self.accept()

            console.log(f"New connection from {addr[0]}:{addr[1]}")

            self.add_client(conn, addr)

    def add_client(self, connection, address):
        console.log("Starting client thread...")

        all_client_data[f"{connection}"] = {}
        clients_list.append(connection)

        client_thread = threading.Thread(target=self.handle_client, args=(connection, address))
        client_thread.start()

    def broadcast(self, data: str):
        for client in clients_list:
            self.send_data(data, client)

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

    def handle_client(self, conn, addr):
        self.handle_starting_comms(conn)

        connected = True

        username = all_client_data[f'{conn}']['username']

        while connected:
            try:
                data_received = self.receive_data(conn)

                if data_received:
                    self.broadcast(f"{username}{MESSAGE_COLON}{data_received}")
            except Exception as e:
                console.log(f"[ EXCEPTION ] {e}")
                connected = False

        self.broadcast(f"{Fore.RED}{all_client_data[f'{conn}']['username']} has disconnected!")

    def handle_starting_comms(self, conn):
        try:
            received_data = self.receive_data(conn)

            console.log(received_data)

            received_data = json.loads(received_data)

            login_method = received_data['method']
            username = received_data['username']
            password = received_data['password']

            # Checking if method to be used
            if login_method == "guest":
                all_client_data[f"{conn}"]['login-type'] = "guest"
                all_client_data[f"{conn}"]['username'] = f"{Fore.LIGHTBLUE_EX}{username}{Style.RESET_ALL}"

                starting_data_to_send = {
                    "allowed": True
                }

                self.broadcast(f'{username} joined the chat!')
            elif login_method == "login":
                verified = self.verify_account(username, password)

                if verified:
                    starting_data_to_send = {
                        "verified": verified
                    }
                    all_client_data[f"{conn}"]['login-type'] = "proper"
                    all_client_data[f"{conn}"]['username'] = f"{Fore.GREEN}{username}{Style.RESET_ALL}"

                    self.broadcast(f'{username} joined the chat!')
                else:
                    starting_data_to_send = {
                        "verified": verified
                    }
            elif login_method == "register":
                self.add_account(username, password)
                self.send_data(f"{Fore.MAGENTA}SERVER{Style.RESET_ALL}{MESSAGE_COLON} Account registered!", conn)
                all_client_data[f"{conn}"]['login-type'] = "new"
                all_client_data[f"{conn}"]['username'] = f"{Fore.YELLOW}{username}{Style.RESET_ALL}"

                starting_data_to_send = {
                    "created": True
                }

                self.broadcast(f'{username} joined the chat!')

            console.log(f"++ RECEIVED ++\n-- Method: {login_method}\n-- Name: {username}\n-- Password: {password}")

            starting_data_json = json.dumps(starting_data_to_send)

            self.send_data(starting_data_json, conn)

            console.log(f"++ SENDING ++\n{starting_data_json}")
        except Exception as e:
            console.log("Error: Unable to handle starting communications for client!")
            console.log(f"Exception: {e}")

#############
# FUNCTIONS #
#############
# def handle_client(conn, addr, username):
#     connected = True
#
#     while connected:
#         message_recv = conn.recv(10).decode(ENCODING_FORMAT)
#         console.log(message_recv)
#
#         try:
#             conn.send("test".encode(ENCODING_FORMAT))
#         except Exception as e:
#             conn.close()
#             connected = False
#
#     console.log(f"{username} has disconnected!")


def on_exit():
    console.log("Exiting...")

    console.log("Closing socket...")
    server.close()
    console.log("Socket closed!")


def run():
    # Global variables
    global server

    server.SERVER_IP = "127.0.1.1"
    server.SERVER_PORT = 5555

    server.start_server()

#########
# OTHER #
#########
if __name__ == "__main__":
    os.system("clear")
    # Registering exiting function
    atexit.register(on_exit)

    server = Server(ENCODING_FORMAT, SERVER_MAX_CONNECTIONS)

    # Running server
    run()
