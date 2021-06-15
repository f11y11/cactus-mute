import discord
from pymongo.errors import DuplicateKeyError
import datetime
from discord.ext import commands, tasks
from .modules.database import col_mutes
from .modules.dtparsing import to_timedelta

guild_id = 692427294261772289
muted_role_id = 725056676725653526

class MuteMongo():
    def __init__(self, _id):
        mute = col_mutes.find_one({"_id": _id})
        if mute:
            self._id = _id
            self._infinite = mute["infinite"]
            self._muted_by = mute["muted_by"]
            self._in_channel = mute["in_channel"]
            self._applied_at = mute["applied_at"]
            self._muted_until = mute["muted_until"]

    def to_dict(self):
        return {
            "_id": self._id,
            "infinite": self._infinite,
            "muted_by": self._muted_by,
            "in_channel": self._in_channel,
            "applied_at": self._applied_at,
            "muted_until": self._muted_until
        }

def apply_mute(user: discord.Member, duration, author: discord.Member, channel: discord.TextChannel):
    """
    I import this function in one of my cogs where it applies mute after warning the user.
    You can get rid of the function entirely if you don't want to import it/apply mutes elsewhere.
    """
    if duration != "0h0m":  # if a duration is specified, try parsing it to retrieve a datetime object.
        try:
            duration_self = datetime.datetime.strptime(duration, "%Hh%Mm")
        except ValueError as e:
            raise e

    mute_dict = {
        "_id": user.id,  # required
        # required, if statement clearly states why is it required.
        "infinite": True if duration.seconds == 0 else False,
        "muted_by": author.id,  # not required
        "in_channel": channel.id,  # required to post unmute message
        "applied_at": datetime.datetime.now(),  # required
        "muted_until": datetime.datetime.now() + datetime.timedelta(hours=duration_self.hour, minutes=duration_self.minute)  # required
    }  # this dictionary will be pushed into mutes column

    try:
        col_mutes.insert_one(mute_dict)
    except DuplicateKeyError:
        current_muted_until = col_mutes.find_one({"_id": user.id})[
            "muted_until"]
        col_mutes.update_one({"_id": user.id}, {"$set": {"muted_until": current_muted_until +
                                                         datetime.timedelta(hours=duration_self.hour, minutes=duration_self.minute)}})
        # updated the existing mute | if it was 30 minutes long, if you muted again for 5 hours after 10 minutes passed, it'll be 5 hours and 20 minutes of mute in total.
    finally:
        print(f"applied mute to {user}")
        return True

class MuteCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.expiration_check.start()

    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def mute(self, ctx, user: discord.Member, duration:to_timedelta = to_timedelta('0s'), *, reason: str = "Unspecified"):
        if duration == True:
            await ctx.send("Invalid string format. Time must be in the form <number>[s|m|h|d|w].")

        mute_dict = {
            "_id": user.id,
            "infinite": True if duration.seconds == 0 else False,
            "muted_by": ctx.author.id,
            "in_channel": ctx.message.channel.id,
            "applied_at": datetime.datetime.now(),
            "muted_until": datetime.datetime.now() + duration
        }

        try:
            await col_mutes.insert_one(mute_dict)
        except DuplicateKeyError:
            _ = await col_mutes.find_one({"_id": user.id})
            current_muted_until = _["muted_until"]
            await col_mutes.update_one({"_id": user.id}, {"$set": {"muted_until": current_muted_until + duration}})
            await ctx.send(f":clock1: Extended **{user}**'s mute by {duration}.")
        else:
            muted_role = ctx.guild.get_role(muted_role_id)
            await user.add_roles(muted_role)
            await ctx.send(f":incoming_envelope: *Applied mute to **{user}** {'for **' + f'{duration}**' if duration.seconds != 0 else 'forever'}. Reason: {reason}*")

    @commands.has_permissions(manage_messages=True)
    @commands.command()
    async def unmute(self, ctx, user: discord.Member):
        await col_mutes.delete_one({"_id": user.id})
        await ctx.send(f"Unmuted `{user}` successfully.")
        muted_role = ctx.guild.get_role(muted_role_id)
        await user.remove_roles(muted_role)

    @tasks.loop(seconds=5)
    async def expiration_check(self):
        # you can replace this variable with a list of dictionaries.
        x = await col_mutes.find({}).to_list(length=None)
        for y in x:  # iterate through every dict in the list
            mute_dict = MuteMongo(_id=y["_id"]).to_dict()
            if not mute_dict["infinite"]:
                guild = self.client.get_guild(guild_id)
                if mute_dict["muted_until"] <= datetime.datetime.now():
                    await col_mutes.delete_one({"_id": mute_dict["_id"]})
                    muted_channel = self.client.get_channel(
                        mute_dict["in_channel"])
                    muted_role = guild.get_role(muted_role_id)
                    user_object = guild.get_member(mute_dict["_id"])
                    await user_object.remove_roles(muted_role)
                    await muted_channel.send(f":alarm_clock: **{user_object}**'s mute just expired.")
                else:
                    try:
                        muted_channel = self.client.get_channel(
                            mute_dict["in_channel"]),
                        user_object = guild.get_member(mute_dict["_id"])
                        muted_role = guild.get_role(muted_role_id)
                        await user_object.add_roles(muted_role)
                    except Exception as e:
                        raise e

def setup(client):
    client.add_cog(MuteCog(client))
