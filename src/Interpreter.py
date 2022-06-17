import matplotlib.pyplot as plt
from matplotlib import use

from .utilities import process, plot

use('TkAgg')


class Interpreter:
    """
    Class responsible for the interpretation of the user's commands and whose role is to be the app's architect,
    coordinating all submodules in order to satisfy the user's requests.
    """

    def __init__(self, collector):
        self._collector = collector
        try:
            self._countries = collector.get_countries(from_disk=True)
        except FileNotFoundError:
            self._countries = collector.get_countries(from_disk=False)
        self._countries["Country"] = self._countries["Country"].str.lower()
        self._countries = self._countries.sort_values(by="Slug", axis='index').set_index(keys=["Country"])
        self._variables = ["active", "deaths", "recovered", "confirmed"]
        self._quit_commands = ["q", "exit", "quit"]
        self._methods = {
            "help": self._interpret_help,
            "plot": self._interpret_plot,
            "sync": self._interpret_sync,
            "list": self._interpret_list
        }

    def interpret(self, requested_action):
        """
        Base method to interpret user.

        This method is a meta-method.
        It redirects to dedicated interpreter for every distinct command.

        :param requested_action: the input string typed by the user.
        :return: boolean equal to True if app exit is requested.
        """
        words = requested_action.split(" ")
        command, arguments = words[0], words[1:]
        if command in self._quit_commands:
            return True
        if command in self._methods.keys():
            self._methods[command](arguments)
        else:
            raise Exception("command '{}' not understood".format(command))

    def _interpret_help(self, args):
        """
        'help' command: prints the interpreter help message.

        **Usage**:
        ```
        help
        ```
        """
        for key, method in self._methods.items():
            print(f"### COMMAND: {key}")
            print(help(method))
            print("")

    def _interpret_sync(self, args):
        """
        'sync' command: synchronize the data between the web API and the local hard drive.

        **Usage**:
        ```
        sync
        ```
        """
        self._collector.synchronize()
        return False

    def _interpret_list(self, args):
        """
        'list' command: prints all modalities of requested variable.

        **Usage**:
        ```
        list [variable1] [variable2] ..
        ```
        The 'list' command can prints the modalities of the following:
        - "countries": prints all countries whose data is available,
        - "variables": prints all variables that can be plotted.
        """
        for argument in args:
            if argument == "variables":
                print(f"AVAILABLE VARIABLES: {self._variables}")
            elif argument == "countries":
                print(f"AVAILABLE COUNTRIES:")
                for country in self._countries.index:
                    print(country)
            else:
                raise Exception(f"unknown variable '{argument}'")
        return False

    def _interpret_plot(self, args):
        """
        'plot' command: draws plot from specific variables & countries specified by user.

        **Usage**:
        ```
        plot [variable1] [variable2] .. for [country1] [country2] ..
        ```
        """
        if "for" in args:
            variables = " ".join(args).split(" for ")[0].split(" ")
            countries = " ".join(args).split(" for ")[1].split(" ")
        else:
            raise Exception("incomplete command, missing the 'for' argument.")

        # ensure variables & countries consistency
        variables = [variable.lower() for variable in variables if variable.lower() in self._variables]
        countries = [country.lower() for country in countries if country.lower() in self._countries.index]

        # get data
        data = self._collector.collect(countries=countries)

        # process data
        data = process(data=data, countries=countries, variables=variables)

        # plot data
        _ = plot(data=data, countries=countries, variables=variables)
        plt.show()

        return False
