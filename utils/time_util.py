# Author: RockMan
# CreateTime: 2024/7/15
# FileName: utils
# Description: This file contains utility functions and classes for the project.

from datetime import datetime, timedelta


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


if __name__ == '__main__':
    # Test the TimeUtil class
    this_month_start, last_month_start, last_month_end = TimeUtil.get_current_and_last_month_dates(
        datetime(2023, 1, 15))
    print(f"This month starts on: {this_month_start}")
    print(f"Last month starts on: {last_month_start}")
    print(f"Last month ends on: {last_month_end}")
