import datetime as dt
import json
import os
import time

import pandas as pd
import requests
from progressbar.bar import ProgressBar

from .error_managment import DataBaseNotFoundError


class DataCollector:
    """
    Class responsible for the interaction between the application and the John Hopkin's University open API.
    """

    def __init__(self, url, folder):
        self._base_url = url
        self._base_folder = folder
        self._status_path = os.path.join(folder, "status.json")

        # check url consistency
        if self._base_url[-1] == "/":
            self._base_url = self._base_url[:-1]
        try:
            requests.request("GET", self._base_url, headers={}, data={}).text.encode("utf8")
        except Exception as error:
            raise DataBaseNotFoundError(destination=self._base_url, message=error)

        # check folder consistency
        if not os.path.isdir(self._base_folder):  # create folder if nonexistent
            os.makedirs(self._base_folder, exist_ok=True)

        # retrieve sync status
        if not os.path.isfile(self._status_path):  # create status file if nonexistent
            self._status = {}
            self._dump_status()
        else:
            self._collect_status()

    def synchronize(self):
        """
        Synchronize data from API and local hard drive.

        Method scans the status file for countries whose data are outdated (i.e. older than current day).
        The data of these countries is then collected from the API and written in the hard drive.

        **Note**: without any subscription, a user is limited in its calls per second to the api.
        Therefore, whenever something goes wrong with the collection, the method pauses for 5 seconds in order to reset that calls per second counter.
        """
        self.dump_countries()
        countries = self.get_countries(from_disk=True)

        bar = ProgressBar(prefix="syncing data: ", max_value=len(countries))
        bar.start()
        i = 0
        for country in countries["Slug"]:
            filepath = os.path.join(self._base_folder, f"{country}.csv")
            if country not in self._status.keys():
                perform_dump = True
            else:
                perform_dump = (not os.path.isfile(filepath)) or (self._status[country] < dt.date.today())
            if perform_dump:
                try:
                    self.dump(country)
                except Exception as error:
                    print(f"  . {country}: {error}.")
                    print("waiting a bit for api to resume connexion")
                    time.sleep(5)
            i += 1
            bar.update(i)
        bar.finish()

    def get_countries(self, from_disk=False):
        """
        Returns pandas dataframe containing description of all available countries.
        :param from_disk: if True, gets the data from the local database.
        :return: pandas.DataFrame describing the available countries.
        """
        if from_disk:
            return self._collect_from_disk(os.path.join(self._base_folder, "countries.csv"))
        else:
            return self._collect_from_api("{}/countries".format(self._base_url))

    def dump_countries(self):
        """Dumps available countries into local drive."""
        filepath = os.path.join(self._base_folder, "countries.csv")
        self.get_countries(from_disk=False).to_csv(filepath, sep=";", header=True, index=False)

    def collect(self, countries, from_disk=False):
        """
        Collects data for a specified countries.

        This methods returns a pandas.DataFrame containing all the variables associated to the specified country.
        It also casts the "Date" column to pandas.datetime, and turns all column labels to lowercase.
        No additional processing is performed on the collected data.

        :param countries: the countries whose data is collected.
        :param from_disk: if true, gets the data from the local database.
        :return: pandas.DataFrame containing the coundrty's daily data.
        """
        data = pd.DataFrame()
        for country in countries:
            if from_disk:
                temp = self._collect_from_disk(os.path.join(self._base_folder, f"{country}.csv"))
            else:
                temp = self._collect_from_api("{}/dayone/country/{}".format(self._base_url, country))
            temp["Date"] = pd.to_datetime(temp["Date"])
            temp = temp.rename(columns={col: col.lower() for col in temp.columns})
            data = pd.concat((data, temp), axis=0)
        return data

    def dump(self, country):
        """
        Dumps data collected for specified country into local drive.

        :param country: the country whose data is dumped.
        :return: None.
        """
        filepath = os.path.join(self._base_folder, "{}.csv".format(country))
        data = self.collect(country, from_disk=False)
        data.to_csv(filepath, sep=";", header=True, index=False)
        self._status[country] = dt.date.today()
        self._dump_status()

    def _dump_status(self):
        """Dump status file on disk."""
        status_str = {key: value.strftime("%y-%m-%d") for (key, value) in self._status.items()}
        with open(self._status_path, "w") as file:
            json.dump(status_str, file)

    def _collect_status(self):
        """Collects status file from disk."""
        with open(self._status_path, "r") as file:
            status_str = json.load(file)
        self._status = {key: dt.datetime.strptime(value, "%y-%m-%d") for (key, value) in status_str.items()}
        for key, value in self._status.items():
            self._status[key] = dt.date(year=value.year, month=value.month, day=value.day)

    @staticmethod
    def _collect_from_api(url):
        try:
            response = requests.get(url)
        except Exception as error:
            raise DataBaseNotFoundError(destination=url, message=error)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            raise Exception(response.text)

    @staticmethod
    def _collect_from_disk(filepath):
        if os.path.isfile(filepath):
            return pd.read_csv(filepath, sep=";", header=0)
        else:
            raise FileNotFoundError(f"cannot find file {filepath}")
