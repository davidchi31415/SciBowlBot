# SciBowlBot

This is a Discord bot that automates practice games. Play with a coach or proctor.
Functionality includes:
* Toss-up and Bonus questions
* Data saving (to local directory)
* Leaderboards (only updated by games with proctor teacher)
* Message delete

Instructions:
Download this directory to your computer and make sure you have Python 3.5 or higher.

1) Go to https://discord.com/developers/applications and create an application. Title it whatever you'd like.
2) Create a Discord server, and then, in the Developer Portal, create an OAuth2 bot invite link with admin permissions.
3) Use this link to add to your server. You should now see the bot in your server but offline.
4) In the same folder as your downloaded folder, run in command line `python -m pip install requirements.txt`.
5) Open, in the downloaded, the file named config.py and edit the lines of code with all letters upper. These are the IDs of your server's information. For instance, `CATEGORY_ID` is needed for the bot to know what category in your server is the right one for starting games. This way, the bot won't clutter up your server in the wrong area. The others are for roles you must create. The Teacher is just a role that serves as a moderator for the bot. Only if proctor has Teacher role do server leaderboards update.
6) Then, install FFmpeg onto your computer. There are many different tutorials for doing this, and steps may seem different according to your operating system. 
7) Run the bot by entering `python main.py` in the same folder, and the bot should be online. You can keep it on as long as it is running on your computer and connected to wifi.

I recommend either hosting on Heroku or on your local machine.
If you have questions, add me on discord. I can help if I'm not busy, just friend `achidchi#0271`.
