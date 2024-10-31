# Author: RockMan
# CreateTime: 2024/7/15
# FileName: utils
# Description: This file contains utility functions and classes for the project.

from datetime import datetime, timedelta, date


# TimeUtil class
# This class contains static methods for handling time-related operations.
class TimeUtil:

    @staticmethod
    def get_current_and_last_month_dates(moment: datetime = datetime.now()) -> tuple[datetime, datetime, datetime]:
        """
        This function returns the start date of the current month and the start and end dates of the last month.

        :param moment: A datetime object representing the current moment. If not provided, defaults to the current
        datetime.
        :type moment: datetime, optional
        :return: A tuple containing three datetime objects.
        The first object is the start date of the current month,
        the second object is the start date of the last month,
        and the third object is the end date of the last month.
        :rtype: tuple[datetime, datetime, datetime]
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
        This function returns the start date of the current year and the start date of the last year.

        :param dates: A datetime object representing the current moment. If not provided, defaults to the current
        datetime.
        :type dates: datetime, optional
        :return: A tuple containing two datetime objects.
        The first object is the start date of the current year,
        and the second object is the start date of the last year.
        :rtype: tuple[datetime, datetime]
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
        This function returns a list of tuples, each containing the start and end dates of each month in the specified year.

        :param year_num: The year for which the monthly start and end dates are to be calculated.
        :type year_num: int
        :return: A list of tuples, where each tuple contains two date objects representing the start and end dates of a month.
        :rtype: list[tuple[date, date]]
        """

        months = []
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        if year_num < current_year:
            for month in range(1, 13):
                start_date = date(year_num, month, 1)
                if month == 12:
                    end_date = date(year_num + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year_num, month + 1, 1) - timedelta(days=1)
                months.append((start_date, end_date))
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
