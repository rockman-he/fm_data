# Author: RockMan
# CreateTime: 2024/7/16
# FileName: market_util.py
# Description: This module contains the MarketUtil class which provides methods for handling market-related operations.

from datetime import datetime
import pandas as pd
from utils.db_util import Constants as C, create_conn, get_raw


class MarketUtil:
    """
    A utility class for handling market-related operations.

    Attributes:
        start_time (datetime.date): The start time for retrieving the Interbank Rate Table (IRT).
        end_time (datetime.date): The end time for retrieving the IRT.
        raw (pd.DataFrame): The raw data retrieved from the database.
    """

    def __init__(self):
        """
        Initialize a MarketUtil instance.

        The start time, end time, and raw data are initialized as None or an empty DataFrame respectively.
        """

        self.start_time = None
        self.end_time = None
        self.raw = pd.DataFrame({})

    def get_irt(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        Retrieve the Interbank Rate Table (IRT) for a given time period.

        Args:
            start_time (datetime.date): The start time for retrieving the IRT.
            end_time (datetime.date): The end time for retrieving the IRT.

        Returns:
            pd.DataFrame: The IRT for the given time period.
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
