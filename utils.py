#######################
# IMPORTING LIBRARIES #
#######################
from pprint import PrettyPrinter
from datetime import datetime
from pprint import pprint

################
# DECLARATIONS #
################
printer = PrettyPrinter()


#############
# FUNCTIONS #
#############
def info_print(data: any) -> None:
    # Print data to screen
    printer.pprint(data)

    # Printing info
    printer.pprint(f"-- Data Type: {type(data)}")
    printer.pprint(f"-- Length: {len(str(data))}")
    printer.pprint(f"-- -- -- -- -- -- -- -- -- -- -- --")


def log(text: str, who: str, category: str, echo=False):
    time = datetime.now().strftime("%H:%M:%S")
    current_time = f"[{time}]"

    log_file_name = "DEBUG_LOGS.txt"

    log_message = f"{current_time} - [ {who.upper()} ] [{category.upper()}] - {text}\n"

    if echo:
        pprint(log_message)

    try:
        with open(f"{log_file_name}", "a") as f:
            f.write(log_message)
    except FileNotFoundError as e:
        print(f"[ INFO ] - Creating new log file({log_file_name})...")

        with open(f"{log_file_name}", "w") as f:
            f.write(log_message)


##################
# SCRIPT TESTING #
##################
if __name__ == "__main__":
    log("some data brrr...", "Sending")
    log("some data errr...", "Receiving")
