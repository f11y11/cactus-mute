# cactus-mute
This repository contains one of the cogs created for Cactus bot - dedicated for muting and unmuting users.

### This repository contains the following:
- Libraries used
- The main function explaining how it works
- Additional (hopefully) helpful comments
- A datetime parsing module (modules/dtparsing.py) created by https://github.com/chrisdewa, here's the module: https://github.com/chrisdewa/dpytools/blob/master/dpytools/parsers.py

### What makes this mute system useful?
- It uses datetime instead of asyncio.sleep and this will make sure the mute is expired and won't result in some users with longer mutes staying muted forever after the bot restarts.
- If an user tries to bypass the @muted role by leaving the server and rejoining, bot re-adds the role to them as long as their mute is not expired.
- With the current time parsing method I used, you can mute users up to 23 hours and 59 minutes but you can add the day parameter yourself to make it up above 24 hours (days longer)
- If you wanted to increase the mute expiration time for an user who is already muted, you can simply re-run mute command and it will longer their existing duration.

### You can
- Modify this code
- Share this code
- Use this code
- Copy its logic to another discord library
- Create pull requests with improved versions of this code
- Comment on this repository


If you want to see this cog in action, you can consider joining the server the bot was made for. [Join here](https://discord.gg/sQVdbX8rBM)

If you need support related to this code/repository, please join [this](https://discord.gg/9aRBdpJ) server and not the server above as [this](https://discord.gg/9aRBdpJ) is my development server.

## Special thanks to
- https://github.com/chrisdewa/ | u/alexdewa
