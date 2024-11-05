# Author: RockMan
# CreateTime: 2024/7/15
# FileName: utils
# Description: This file contains utility functions and classes for the project.

from datetime import datetime, timedelta, date


class TimeUtil:

    @staticmethod
    def get_current_and_last_month_dates(moment: datetime = datetime.now()) -> tuple[datetime, datetime, datetime]:
        """
        返回当前月份的开始日期，以及上个月的开始和结束日期。

        :param moment: 基准时间的 datetime 对象，默认为当前 datetime。
        :return: 包含三个 datetime 对象的元组。
        第一个是当前月份的开始日期，
        第二个是上个月的开始日期，
        第三个是上个月的结束日期。
        tuple[datetime, datetime, datetime]

        """

        # Calculate the start date of the current month
        func_this_month_start = datetime(moment.year, moment.month, 1)
        # Calculate the end date of the last month
        func_last_month_end = func_this_month_start - timedelta(days=1)
        # Calculate the start date of the last month
        func_last_month_start = datetime(func_last_month_end.year, func_last_month_end.month, 1)
        # Return the start date of the current month, the start date and the end date of the last month
        return func_this_month_start, func_last_month_start, func_last_month_end

    @staticmethod
    def get_current_and_last_year(dates: datetime = datetime.now()) -> tuple[datetime, datetime]:
        """
        该函数返回当前年份的开始日期和去年的开始日期。

        :param dates: 基准时间的 datetime 对象，默认为当前 datetime。
        :type dates: datetime, optional
        :return: 包含两个 datetime 对象的元组。
        第一个对象是当前年份的开始日期，
        第二个对象是去年的开始日期。

        """
        # Calculate the start date of the current year
        func_this_year_start = datetime(dates.year, 1, 1)
        # Calculate the start date of the last year
        func_last_year_start = datetime(dates.year - 1, 1, 1)
        # Return the start date of the current year and the start date of the last year
        return func_this_year_start, func_last_year_start

    @staticmethod
    def get_months_feday(year_num: int) -> list[tuple[date, date]]:
        """
        该函数返回一个包含元组的列表，每个元组包含指定年份中每个月的开始和结束日期（截至到前一天（含））

        :param year_num: 要计算每月开始和结束日期的年份。
        :type year_num: int
        :return: 一个包含元组的列表，每个元组包含表示某个月的开始和结束日期的两个日期对象。

        """

        months = []
        # 时间截点为前一天的数据
        current_date = datetime.now() - timedelta(days=1)
        current_year = current_date.year
        current_month = current_date.month

        # 非当前年的处理
        if year_num < current_year:
            for month in range(1, 13):
                start_date = date(year_num, month, 1)
                if month == 12:
                    end_date = date(year_num + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year_num, month + 1, 1) - timedelta(days=1)
                months.append((start_date, end_date))
        # 当前年处理
        else:
            for month in range(1, current_month + 1):
                start_date = date(year_num, month, 1)
                if month == current_month:
                    end_date = current_date.date() - timedelta(days=1)
                else:
                    end_date = date(year_num, month + 1, 1) - timedelta(days=1)

                if end_date < start_date:
                    end_date = start_date

                months.append((start_date, end_date))

        return months


if __name__ == '__main__':
    # Test the TimeUtil class
    # this_month_start, last_month_start, last_month_end = TimeUtil.get_current_and_last_month_dates(
    #     datetime(2023, 1, 15))
    # print(f"This month starts on: {this_month_start}")
    # print(f"Last month starts on: {last_month_start}")
    # print(f"Last month ends on: {last_month_end}")

    print(TimeUtil.get_months_feday(2023))
