from bs4 import BeautifulSoup
import json
import requests
import re
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
from twill.commands import *
import os

class Scraper:
    """
        EmpLive ESS home page web scraper.

        This class opens a browser using Twill
        to access EmpLive ESS remotely using
        your login credentials, then extracts
        raw HTML from the website and reads
        it with BeautifulSoup.
    """

    def __init__(self, username, password):
        """
            Opens a new browser with Twill and logs into EmpLive ESS.

            Args:
                username (str): EmpLive ESS username. Format: ``user@domain``.
                password (str): EmpLive ESS password.
            
            Returns:
                None
        """
        reset_browser()
        go("https://ess.emplive.net/")

        fv('1', '_txtUsername', username)
        fv('1', '_txtPassword', password)
        submit()

        try:
            not_find("_tblErrorTable") # This element only appears if login fails.
        except Exception as e:
            raise Exception("401 Unauthorised\nForbidden from accessing EmpLive roster, check token.json is correct.")
        
        code('200')

        follow("Personal Roster")
        code('200')

    def next_period(self):
        """
        Navigate to the next week's shift roster.
        """
        submit("_content_ctl09__filtersPersonal__btnForward")
        reload()
    
    def prev_period(self):
        """
        Navigate to the previous week's shift roster.
        """
        submit("_content_ctl09__filtersPersonal__btnBack")
        reload()

    def get_roster_page(self, tmp_file = "tmp/Home.aspx"):
        """
            Gets the entire EmpLive ESS employee home page as raw HTML code.
            Uses the user token stored in token.json.

            Args:
                tmp_file (str) : Where to temporarily store the HTML webpage file.
            
            Returns:
                page (BeautifulSoup) : The scraped home page.
        """

        # Create folder for output file if not exists
        tmp_dir, _ = os.path.split(tmp_file)
        os.makedirs(tmp_dir, exist_ok=True)

        save_html(tmp_file) # Print the web HTML data to console output.
        
        with open(tmp_file, "r") as f:
            raw_data = f.read()
            f.close()

        os.remove(tmp_file)
        os.removedirs(tmp_dir)

        soup = BeautifulSoup(raw_data, 'html5lib')

        if "Error" in soup.title.string:
            raise Exception("400 Bad Request\nUnknown error accessing EmpLive roster, check token.json is correct.")
        
        if "Access Denied" in soup.title.string:
            raise Exception("401 Unauthorised\nForbidden from accessing EmpLive roster, check token.json is correct.")

        if "Session Timed Out" in soup.title.string:
            raise Exception("408 Request Timeout\nASP.NET Session has timed out, create a new session token by logging in.")

        return soup

class Extractor:
    """
        Parses usable data structures
        out of EmpLive HTML dumps.
    """
    def __init__(self):
        pass
    
    def parse_roster_dates(self, roster):
        """
        Given an EmpLive employee roster as DataFrame,
        converts "Start Date" and "End Date" columns
        from string type to datetime type and removes
        redundant "Date" and "Roster" columns.
        
        Args:
            roster (DataFrame): The roster with string columns for "Start Date" and "End Date".
        
        Returns:
            roster (DataFrame): The roster with datetime columns for "Start Date" and "End Date".
        """
        current_year = datetime.today().year

        for i, shift in enumerate(roster.to_dict(orient='records')):
            start_time_str = f"{shift["Date"]} {current_year}, {shift["Start Time"]}"
            end_time_str = f"{shift["Date"]} {current_year}, {shift["End Time"]}"
            
            start_time = pd.to_datetime(start_time_str, format='%a, %b %d %Y, %H:%M')
            end_time = pd.to_datetime(end_time_str, format='%a, %b %d %Y, %H:%M')

            roster.loc[i, "Start Time"] = start_time
            roster.loc[i, "End Time"] = end_time

        del roster["Date"]
        del roster["Roster"]

        return roster

    def parse_roster_html_table(self, roster_html_table):
        """
            Converts a HTML employee roster table into a DataFrame.

            Args:
                roster_html_table (bs4.element.Tag): A raw HTML employee roster table scraped from the EmpLive ESS home page.
            
            Returns:
                roster (DataFrame): The same roster parsed as a DataFrame.
        """
        roster_table_rows = roster_html_table.find_all('tr')
        roster_table_head = roster_table_rows[0]
        roster_table_data = roster_table_rows[1:]

        headings = {h.string : None for h in roster_table_head.find_all('th')}

        shifts = []
        for row in roster_table_data:

            shift = headings.copy()

            row_data = row.find_all('td')

            row_text = [i.find('span') for i in row_data]
            row_strings = [i.string if i is not None else None for i in row_text]

            for i, key in enumerate(shift.keys()):
                shift[key] = row_strings[i]
            
            shifts.append(shift)

        shifts = pd.DataFrame(shifts)

        # Convert dates from string format to datetime format.
        shifts = self.parse_roster_dates(shifts)

        return shifts
    
    def get_roster(self, home_page : BeautifulSoup):
        """
            Get the roster table from the EmpLive ESS scrape and convert it to a DataFrame.

            Args:
                home_page (BeautifulSoup): A web scrape of the EmpLive ESS home page.
            
            Returns:
                roster (DataFrame | None): The employee's roster.
        """

        roster_table = home_page.find('table', id=re.compile('[a-zA-Z0-9_-]*gridPersonalRoster'))

        if roster_table is None:
            return None
            #raise Exception("Unable to find employee roster table in web scrape.")

        roster_table = home_page.find('table', id=re.compile('[a-zA-Z0-9_-]*gridPersonalRoster'))

        roster = self.parse_roster_html_table(roster_table)

        return roster
    
    def get_period(self, home_page : BeautifulSoup):

        """
            The EmpLive ESS website can only display rosters one week ("period")
            at a time. This method returns the date of the currently selected
            period from the EmpLive website as a datetime.

            Args:
                home_page (BeautifulSoup): A web scrape of the EmpLive ESS home page.
            
            Returns:
                start_date (datetime)
        """
        # Extract the period date strings
        period_start = home_page.find("span", id ="_content_ctl09__filtersPersonal__lblStartDate").string
        period_end = home_page.find("span", id ="_content_ctl09__filtersPersonal__lblEndDate").string

        # Convert to datetime
        period_start = pd.to_datetime(period_start, format='%d %b %Y')
        period_end = pd.to_datetime(period_end, format='%d %b %Y')

        return period_start#, period_end

class EmpKiller:
    """
        API for EmpLive ESS.
        This class opens a browser to access EmpLive ESS remotely using your login credentials.
    """
    def __init__(self, login_data):
        """
            Opens a new browser and logs into EmpLive ESS.

            Args:
                login_data (str): The file path to a json file storing your username and password.
            
            Returns:
                None
        """
        with open(login_data) as f:
            data = json.load(f)
            f.close()
        
        self.sc = Scraper(data.get("username"), data.get("password"))
        self.ex = Extractor()
        self.reload_page()

    def reload_page(self):
        """
            Reloads the EmpLive ESS webpage.
            This is needed to update the roster table after
            selecting the 'Next Period' or 'Previous Period' buttons.

            Args:
                None
            
            Returns:
                None
        """
        self.page = self.sc.get_roster_page()
    
    def get_period(self):
        """
            The EmpLive ESS website can only display rosters one week ("period")
            at a time. This method returns the date of the currently selected
            period from the EmpLive website as a datetime.

            Args:
                None

            Returns:
                period (datetime): The starting day of the current roster.
        """
        return self.ex.get_period(self.page)

    def go_to_week(self, starting_date, max_reloads = 10):
        """
            Use the EmpLive website to access the roster
            for any given week (period) starting at ``starting_date``.

            Since EmpLive can only display one week (period)
            of your roster at once, we must *manually click*
            the "Next / Previous Period" buttons on the roster
            page to navigate to the roster for any given week.

            Args:
                starting_date (datetime):
                    The starting date for which week's roster you want to view.
                    This date will automatically be converted to first day of the week if it is not already.
                max_reloads (int):
                    The maximum number of times this function may press the "Next / Previous Period"
                    buttons on the EmpLive website to find the target roster period.
                    If we don't reach the target period in time, this *will raise an Exception*!

            Returns:
                None
        """
        # Make starting_date the first day of the week.
        starting_date = starting_date - timedelta(days=starting_date.weekday())
        starting_date = starting_date.replace(hour=0, minute=0, second=0, microsecond=0)

        website_date = self.get_period()
        
        # print(f"Website period: {website_date.strftime("%d/%m/%Y %I:%M:%S")}")
        # print(f"Desired period: {starting_date.strftime("%d/%m/%Y %I:%M:%S")}")
        # print(f"Difference: {(website_date - starting_date).days} days")

        i = 0
        while abs((website_date - starting_date).days) > 0:

            if website_date < starting_date:
                self.sc.next_period()
            else:
                self.sc.prev_period()
            self.reload_page()
            website_date = self.get_period()

            i+= 1
            if i > max_reloads:
                raise Exception(f"Could not reach desired period within {max_reloads} reloads.")
                
            # print(f"Website period: {website_date.strftime("%d/%m/%Y %I:%M:%S")}")
            # print(f"Desired period: {starting_date.strftime("%d/%m/%Y %I:%M:%S")}")
            # print(f"Difference: {(website_date - starting_date).days} days")

    def get_roster_by_date(self, starting_date : datetime = datetime.today(), max_reloads = 10):
        """
            Get *one week*'s roster from the EmpLive website using a starting date.

            Args:
                starting_date (datetime): 
                    The starting date for which week's roster you want to obtain.
                    This date will automatically be converted to first day of the week if it is not already.
                max_reloads (int):
                    The maximum number of times this function may press the "Next / Previous Period"
                    buttons on the EmpLive website to find the target roster period.
                    If we don't reach the target period in time, this *will raise an Exception*!
            
            Returns:
                roster (DataFrame | None):
                    The weekly roster as a DataFrame, or *None* if no roster exists for the given week.
        """
        self.go_to_week(starting_date, max_reloads=max_reloads)
        self.reload_page()
        return self.ex.get_roster(self.page)
    
    def get_roster(self, weeks_ahead = 0, max_reloads=10):
        """
            Get *the current week*'s roster from the EmpLive website.

            Args:
                weeks_ahead (int): 
                    How many weeks to look ahead or behind when obtaining the roster.
                    The value ``1`` will return *next* week's roster, ``-1`` returns *last* week's roster, etc.
                max_reloads (int):
                    The maximum number of times this function may press the "Next / Previous Period"
                    buttons on the EmpLive website to find the target roster period.
                    If we don't reach the target period in time, this *will raise an Exception*!
            
            Returns:
                roster (DataFrame | None):
                    The weekly roster as a DataFrame, or *None* if no roster exists for the given week.
        """
        starting_date = datetime.today() + timedelta(days = weeks_ahead * 7)
        return self.get_roster_by_date(starting_date, max_reloads=max_reloads)