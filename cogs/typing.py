import asyncio
import datetime

from disnake import ApplicationCommandInteraction, Message, DMChannel, Thread, NotFound, HTTPException, Thread, User, \
    Member, ForumChannel
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog

modmail_forum_id: int = 1118969274527133808


class Typing(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} | {__name__}")

    async def get_modmail_thread(self, user: User | Member) -> Thread | None:
        thread = None
        modmail_forum = self.bot.get_channel(modmail_forum_id)
        for mod_thread in modmail_forum.threads:
            if (str(user.id) in mod_thread.name) and (not mod_thread.archived):
                thread = mod_thread
                break

        return thread

    @commands.Cog.listener("on_typing")
    async def on_user_typing(self, channel, user, when: datetime.datetime):
        thread = await self.get_modmail_thread(user)

        if thread is None:
            return

        if thread.parent_id == modmail_forum_id:
            return



        await thread.trigger_typing()

    @commands.Cog.listener("on_typing")
    async def on_agent_typing(self, channel, user, when: datetime.datetime):
        if not isinstance(channel, Thread):
            return

        if not channel.parent_id == modmail_forum_id:
            return

        dm = await user.create_dm()
        await dm.trigger_typing()


def setup(bot: Bot) -> None:
    bot.add_cog(Typing(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
