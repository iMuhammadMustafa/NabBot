import asyncio
import re

import discord
from discord.ext import commands

from config import lite_mode
from utils import checks
from utils.database import *
from utils.tibia import tibia_worlds


class Admin:
    """Commands for server owners and admins"""
    def __init__(self, bot: discord.Client):
        self.bot = bot

    @commands.group(name="setworld", pass_context=True, no_pm=True)
    @checks.is_admin()
    @checks.is_not_lite()
    @asyncio.coroutine
    def set_world(self, ctx: commands.Context, *, world: str = None):
        """Sets this server's Tibia world.

        If no world is passed, it shows this server's current assigned world."""
        server_id = ctx.message.server.id
        if world is None:
            current_world = tracked_worlds.get(server_id, None)
            if current_world is None:
                yield from self.bot.say("This server has no tibia world assigned.")
            else:
                yield from self.bot.say("This server has **{0}** assigned.".format(current_world))
            return

        if world.lower() in ["clear", "none", "delete", "remove"]:
            yield from self.bot.say("Are you sure you want to delete this server's tracked world? `yes/no`")
            reply = yield from self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel,
                                                         timeout=50.0)
            if reply is None:
                yield from self.bot.say("I guess you changed your mind...")
                return
            elif reply.content.lower() not in ["yes", "y"]:
                yield from self.bot.say("No changes were made then.")
                return
            c = userDatabase.cursor()
            try:
                c.execute("DELETE FROM server_properties WHERE server_id = ? AND name = 'world'", (server_id,))
            finally:
                c.close()
                userDatabase.commit()
            yield from self.bot.say("This server's tracked world has been removed.")
            reload_worlds()
            return

        world = world.strip().capitalize()
        if world not in tibia_worlds:
            yield from self.bot.say("There's no world with that name.")
            return
        yield from self.bot.say("Are you sure you want to assign **{0}** to this server? "
                                "Previous worlds will be replaced.".format(world))
        reply = yield from self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel,
                                                     timeout=50.0)
        if reply is None:
            yield from self.bot.say("I guess you changed your mind...")
            return
        elif reply.content.lower() not in ["yes", "y"]:
            yield from self.bot.say("No changes were made then.")
            return

        c = userDatabase.cursor()
        try:
            # Safer to just delete old entry and add new one
            c.execute("DELETE FROM server_properties WHERE server_id = ? AND name = 'world'", (server_id,))
            c.execute("INSERT INTO server_properties(server_id, name, value) VALUES (?, 'world', ?)",
                      (server_id, world,))
            yield from self.bot.say("This server's world has been changed successfully.")
        finally:
            c.close()
            userDatabase.commit()
            reload_worlds()


def setup(bot):
    bot.add_cog(Admin(bot))