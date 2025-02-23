# EmpKiller - EmpLive Roster API with Google Calendar Exporting
Hate using EmpLive's terrible mobile app to see your work roster? EmpKiller is for you.

This application acts as an API you can use to retrieve your EmpLive roster without having to use their awful user interface.

You can use this app to retrieve your EmpLive roster data and export this data to Google Calendar using the Google Calendar API, but you will need to create a Google Calendar API token to do so.

EmpKiller does NOT currently support creating leave requests, only viewing which shifts you have been rostered to do.

# Installation
- Install Python 3.12+
- Run ```pip install requirements.txt``` within the root directory of this repo to install the needed Python libraries.
- Modify ``account.json`` to contain your EmpLive username and password.
    - This info is used by EmpKiller **only** to login to EmpLive ESS to retrieve your roster and is **not** sent anywhere else. Trust me.
- Create an Google Cloud API token using [this tutorial](https://youtu.be/B2E82UPUnOY).
- Success!

# Usage
```bash
from empkiller import EmpKiller, GoogleCalendar
emp = EmpKiller('account.json') # Log-in credentials file
roster = emp.get_roster(0) # Get working roster for this week

roster

> Start Time	End Time	Role	Department	Sub Department	Job	Status	Comments
> 0	2025-02-21 17:00:00	2025-02-21 19:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None
> 1	2025-02-22 17:00:00	2025-02-22 21:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None

# emp.get_roster(1) # Get working roster for next week
# emp.get_roster(2) # Get working roster for the week after next
# emp.get_roster(-1) # Get working roster for last week

cal = GoogleCalendar('credentials.json') # Access Google Calendar via the Python API using an API token (not provided).

cal.add_roster(roster, reminder_time=120) # Add this week's roster to my Google Calendar and give me two hour reminders before each shift.
```

# TODO
- Fix bugs
- Make Google Calendar integration less terrible
