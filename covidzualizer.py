import os

from src import DataCollector
from src import Interpreter

VERSION = "0.3.0"

URL = "https://api.covid19api.com"
FOLDER = os.path.join(os.path.expanduser('~'), ".covidzualizer")
GREETER = "Welcome to CovidVisualizer!"
SPLITTER = "#" * len(GREETER)


if __name__ == "__main__":
    collector = DataCollector(url=URL, folder=FOLDER)
    interpreter = Interpreter(collector=collector)

    # Greet user
    print(SPLITTER)
    print(GREETER)
    print(SPLITTER)
    print("  . version: {}".format(VERSION))
    print("  . base url: {}".format(URL))
    print("  . base folder: {}".format(FOLDER))

    # start interpreter
    exit_requested = False
    while not exit_requested:
        answer = input("> ")
        try:
            exit_requested = interpreter.interpret(answer)
        except Exception as e:
            print("error: {}".format(e))
            exit_requested = False
    print("See you later !")
