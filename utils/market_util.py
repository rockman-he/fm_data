# Author: RockMan
# CreateTime: 2024/7/16
# FileName: market_util.py
# Description: This module contains the MarketUtil class which provides methods for handling market-related operations.

from datetime import datetime
import pandas as pd
from utils.db_util import Constants as C, create_conn, get_raw


class MarketUtil:
    """
    一个用于处理市场数据的工具类。


    Attributes:
        start_time (datetime.date): 统计开始时间。
        end_time (datetime.date): 统计结束时间。
        raw (pd.DataFrame): 从数据库中检索的原始数据。
    """

    def __init__(self):
        """
        构造函数
        """

        self.start_time = None
        self.end_time = None
        self.raw = pd.DataFrame({})
        self.conn = create_conn()

    def get_irt(self, start_time: datetime.date, end_time: datetime.date) -> pd.DataFrame:

        """
        获取资金市场各品种利率.

        Args:
            start_time (datetime.date): 统计开始时间。
            end_time (datetime.date): 统计结束时间。

        Returns:
            pd.DataFrame: [C.DATE, C.R001, C.R007, C.SHIBOR_ON, C.SHIBOR_1W]。
        """

        self.start_time = start_time
        self.end_time = end_time

        if self.start_time > self.end_time:
            return pd.DataFrame({})

        if not self.raw.empty:
            return self.raw

        sql = "select * from fm_da.market_irt mi"

        self.raw = get_raw(self.conn, sql)

        full_range = pd.date_range(start=start_time, end=end_time)

        self.raw = self.raw.set_index(C.DATE).resample('D').asfreq().reset_index()
        self.raw.ffill(inplace=True)

        market = self.raw.set_index(C.DATE).reindex(full_range)
        market.index.name = C.DATE

        last_valid_index = market[C.SHIBOR_ON].last_valid_index()

        if last_valid_index is None:
            market[:] = 0.0
        elif last_valid_index < market.index[-1]:
            mask = last_valid_index + pd.Timedelta(days=1)
            market.loc[mask:] = 0.0

        market = market.ffill()

        # # Fill in any missing dates in the DataFrame
        # self.raw = self.raw.set_index(C.DATE).resample('D').asfreq().reset_index()
        # # Forward fill to fill in any missing values
        # self.raw.ffill(inplace=True)
        # Filter the DataFrame to only include rows within the given time period

        market = market.reset_index()

        mask = (market[C.DATE] >= pd.to_datetime(self.start_time)) & (
                market[C.DATE] <= pd.to_datetime(self.end_time))

        return market.loc[mask]


if __name__ == '__main__':
    # Test the MarketUtil class
    market = MarketUtil()
    start_time = datetime(2024, 6, 1)
    end_time = datetime(2024, 6, 1)
    print(market.get_irt(start_time, end_time))
