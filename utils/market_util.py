# Author: RockMan
# CreateTime: 2024/7/16
# FileName: market_util.py
# Description: This file contains the MarketUtil class which provides methods for handling market-related operations.
# The class includes methods for initializing the class and retrieving the Interbank Rate Table (IRT)
# for a given time period.
# The file is part of a larger project and is authored by RockMan.
from datetime import datetime

import pandas as pd

from utils.db_util import Constants as C, create_conn, get_raw


class MarketUtil:
    """
    This class contains static methods for handling market-related operations.
    """

    def __init__(self):
        """
        Constructor for the MarketUtil class.

        Initializes the start time, end time, and raw data as None or an empty DataFrame respectively.
        """

        self.start_time = None
        self.end_time = None
        self.raw = pd.DataFrame({})

    def get_irt(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """
        Method to get the Interbank Rate Table (IRT) for a given time period.

        Args:
            start_time (datetime): The start of the time period.
            end_time (datetime): The end of the time period.

        Returns:
            pd.DataFrame: A DataFrame containing the IRT for the given time period.

        This method first checks if the start time is later than the end time,
        in which case it returns an empty DataFrame.
        Otherwise, it executes a SQL query to get the IRT from the 'fm_da.market_irt mi' table.
        The resulting DataFrame is then resampled to fill in any missing dates,
        forward filled to fill in any missing values,
        and finally filtered to only include rows within the given time period.
        """
        self.start_time = start_time
        self.end_time = end_time

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        if self.raw.empty is False:
            return self.raw

        sql = "select * from fm_da.market_irt mi"

        self.raw = get_raw(create_conn(), sql)
        # Fill in any missing dates in the DataFrame
        self.raw = self.raw.set_index(C.DATE).resample('D').asfreq().reset_index()
        # Forward fill to fill in any missing values
        self.raw.ffill(inplace=True)
        # Filter the DataFrame to only include rows within the given time period
        mask = (self.raw[C.DATE] >= pd.to_datetime(self.start_time)) & (
                self.raw[C.DATE] <= pd.to_datetime(self.end_time))

        return self.raw.loc[mask]


if __name__ == '__main__':
    # Test the MarketUtil class
    market = MarketUtil()
    start_time = datetime(2023, 1, 1)
    end_time = datetime(2023, 6, 1)
    print(market.get_irt(start_time, end_time))
    # print(f"This month starts on: {this_month_start}")
    # print(f"Last month starts on: {last_month_start}")
    # print(f"Last month ends on: {last_month_end}")
