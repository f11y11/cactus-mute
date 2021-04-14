# apply_mute function is not used in command that is executed on discord but it is exactly the same code and it was originally created to mute users remotely through CactusAPI. Not required and you can get rid of it.
# you can use this code/cog directly in your code, you can modify it and/or convert it to other discord libraries if you don't use python but wanted to see how this bot handles mutes.
# I accept pull requests that aim to make this code much better that it is and I accept suggestions and open to any comments.
# database used in this cog is MongoDB but you can make it work with any database similar to MongoDB when it comes to processing data, I believe you can use JSON as well.

# if you want to thank me for this code and/or support me, you can consider starring the repository and sharing it! <3

import discord
from pymongo.errors import DuplicateKeyError # I used pymongo.errors.DuplicateKeyError to check if user has an active mute without having to check it manually to avoid some lines of code.
from datetime import datetime
import datetime as dt
from discord.ext import commands
from discord.ext import tasks # tasks will be used to check mute expirations every 5 seconds.
from .modules.database import col_mutes # importing the mutes column from database module | not required if you're using json.

def apply_mute(user:discord.Member, duration, author:discord.Member, channel:discord.TextChannel):
    if duration != "0h0m": # if a duration is specified, try parsing it to retrieve a datetime object.
        try:
            duration_self = datetime.strptime(duration, "%Hh%Mm")
            duration_dt = dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute)
        except ValueError as e:
            raise e
            
    mute_dict = {
            "_id":user.id, # required
            "infinite": True if duration is "0h0m" else False, # required, if statement clearly states why is it required.
            "muted_by": author.id, # not required 
            "in_channel": channel.id, # required to post unmute message
            "applied_at": datetime.now(), # required
            "muted_until": datetime.now() + dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute) # required
        } # this dictionary will be pushed into mutes column
        
    try:
        col_mutes.insert_one(mute_dict)
    except DuplicateKeyError:
        current_muted_until = col_mutes.find_one({"_id":user.id})["muted_until"]
        col_mutes.update_one({"_id":user.id}, {"$set":{"muted_until":current_muted_until + dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute)}})
        # updated the existing mute | if it was 30 minutes long, if you muted again for 5 hours after 10 minutes passed, it'll be 5 hours and 20 minutes of mute in total.
    finally:
        print(f"applied mute to {user}")
        return True
        
# start from this part if you don't need apply_mute function | both are exactly the same

class Mute(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.expiration_check.start()

    @commands.has_any_role(692445395158040627, 726851208496807996, 692446044042297445, 745629147124072559, 705406153856778331) # jimmy's cult staff roles. you can change this line entirely with commands.has_permissions or your own staff roles.
    @commands.command()
    async def mute(self, ctx, user:discord.Member, duration="0h0m", *, reason:str="Unspecified"):
        if duration != "0h0m":
            try:
                duration_self = datetime.strptime(duration, "%Hh%Mm")
                duration_dt = dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute)
            except ValueError:
                await ctx.send("Please specify mute duration in the following format `%Hh%Mm`")

        mute_dict = {
            "_id":user.id,
            "infinite": True if duration is "0h0m" else False,
            "muted_by": ctx.author.id,
            "in_channel": ctx.message.channel.id,
            "applied_at": datetime.now(),
            "muted_until": datetime.now() + dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute)
        }

        try:
            col_mutes.insert_one(mute_dict)
        except DuplicateKeyError:
            current_muted_until = col_mutes.find_one({"_id":user.id})["muted_until"]
            col_mutes.update_one({"_id":user.id}, {"$set":{"muted_until":current_muted_until + dt.timedelta(hours=duration_self.hour, minutes=duration_self.minute)}})
            await ctx.send(f":clock1: Extended **{user}**'s mute {duration_self.strftime('%H more hours and %M minutes.')}")
        else:
            muted_role = ctx.guild.get_role(725056676725653526)
            await user.add_roles(muted_role)
            await ctx.send(f":incoming_envelope: *Applied mute to **{user}** {'for **' + duration_self.strftime('%Hh %Mm**') if duration != 0 else 'forever'}. Reason: {reason}*")
            
    @commands.has_any_role(692445395158040627, 726851208496807996, 692446044042297445, 745629147124072559, 705406153856778331)
    @commands.command()
    async def unmute(self, ctx, user:discord.Member):
        col_mutes.delete_one({"_id":user.id})
        await ctx.send(f"Unmuted `{user}` successfully.")
        muted_role = ctx.guild.get_role(725056676725653526)
        await user.remove_roles(muted_role)


    @tasks.loop(seconds=5) # loop that checks if someones mute expired or not
    async def expiration_check(self):
        x = col_mutes.find({})
        for y in x:
            if y["infinite"] != True:
                guild = self.client.get_guild(692427294261772289)
                if  y["muted_until"] <= datetime.now():
                    print(y["muted_until"] - datetime.now(), datetime.now() - y["muted_until"])
                    col_mutes.delete_one({"_id":y["_id"]})
                    muted_channel = self.client.get_channel(y["in_channel"])
                    muted_role = guild.get_role(725056676725653526)
                    user_object = guild.get_member(y["_id"])
                    await user_object.remove_roles(muted_role)
                    await muted_channel.send(f":alarm_clock: **{user_object}**'s mute just expired.")
                else:
                    try:
                        muted_channel = self.client.get_channel(y["in_channel"]),
                        user_object = guild.get_member(y["_id"])
                        muted_role = guild.get_role(725056676725653526)
                        await user_object.add_roles(muted_role)
                    except Exception as e:
                        raise e

def setup(client):
    client.add_cog(Mute(client))
