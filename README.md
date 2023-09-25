# Python Discord Mirror Bot

## A fully functional Python script that enables you to mirror any desired Discord channel onto another server. This powerful tool is capable of cloning all message types, including webhooks.

This project is an example which was created to enable anyone to understand how Discord Mirror's work and what's behind them. Every part of the code is in charge of some specific requirements:

* Automatically creates task file (CSV)
* Verify task information given by the user
* Retrieve and compare corresponding messages from the Discord API
* Identify and extract messages
* Send (Mirror) the new messages to the server

## How to run:

Here's a short guide on how you can run the Script by yourself!

1. Clone this project
2. Change directory to the project
3. Install requirements with : pip install -r requirements.txt
4. Fill in the task.csv file
5. Run the main.py file

## Further information

#### How do I obtain the Account Token?

1. Head onto your Discord App , click Shift + i
2. Go to network tab and search for science (it's an api call)
3. Refresh the site , f5
4. Search for the science call and search for Authorization in Request Headers

![discord_token](https://github.com/oscarsebastian/Discord-Miror-Bot/assets/58465405/b14e4152-4c36-4ee8-87af-cbe0f5606209)

#### How do I obtain the Channel Id?

1. Turn on developper mode in Discord Settings
2. Right click on the given channel and click (Copy Channel Id)

#### Features

* Select incognito_mode to True if you dont want the true username or avatar to show up in the mirrored channel (Anonimous)
* You can also select the desired request delay in the delay columns

##  DISCLAIMER

**IMPORTANT:** Mirroring Discord channels, including the use of this script, may be against Discord's Terms of Service (TOS). This project is intended solely for educational purposes, and the creator assumes no responsibility for any potential account bans resulting from its use. For your safety, it is strongly advised to use a burner Discord account when experimenting with this script, as sharing your account token with anyone could grant them full control of your account, even if two-factor authentication (2FA) is enabled. Always exercise caution and adhere to Discord's policies and guidelines.


