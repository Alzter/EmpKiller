# EmpKiller - EmpLive ESS Roster API
Hate using EmpLive's terrible mobile app to see your work roster? EmpKiller is for you.

This application acts as an API you can use to retrieve your EmpLive roster without having to use their awful user interface.

It does NOT currently support creating leave requests, only viewing which shifts you have been rostered to do.

Currently, the app returns your EmpLive roster as a DataFrame (the Python equivalent to an Excel spreadsheet), but I plan to add Google Calendar export functionality soon.

# Installation
- Install Python 3.12+
- Run ```pip install requirements.txt``` within the root directory of this repo to install the needed Python libraries.
- Modify ``account.json`` to contain your EmpLive username and password.
    - This info is used by EmpKiller **only** to login to EmpLive ESS to retrieve your roster and is **not** sent anywhere else. Trust me.
- Success!

# Usage
```bash
from empkiller import EmpKiller
emp = EmpKiller('account.json') # Log-in credentials file
emp.get_roster(0) # Get working roster for this week

Start Time	End Time	Role	Department	Sub Department	Job	Status	Comments
0	2025-02-21 17:00:00	2025-02-21 19:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None
1	2025-02-22 17:00:00	2025-02-22 21:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None

emp.get_roster(1) # Get working roster for next week

Start Time	End Time	Role	Department	Sub Department	Job	Status	Comments
0	2025-02-28 17:00:00	2025-02-28 21:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None
1	2025-03-01 17:00:00	2025-03-01 21:00:00	NF Sales Ass Cashier	NF Grocery	NF Cashiers	CASHIER ID 123	None	None

emp.get_roster(2) # Get working roster for the week after next
emp.get_roster(-1) # Get working roster for last week

# You get the idea...
```

# TODO
- Google Calendar export functionality
