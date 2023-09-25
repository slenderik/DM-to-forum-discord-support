from time import time, mktime
from cogs.AI import ai_answer

from disnake import Message, DMChannel, HTTPException, Thread, User, \
    Member, Embed, ForumChannel
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog


class Thread:
    """Represents a discord Modmail thread"""

    def __init__(
        self,
        manager: "ThreadManager",
        recipient: typing.Union[discord.Member, discord.User, int],
        channel: typing.Union[discord.DMChannel, discord.TextChannel] = None,
        other_recipients: typing.List[typing.Union[discord.Member, discord.User]] = None,
    ):
        self.manager = manager
        self.bot = manager.bot
        if isinstance(recipient, int):
            self._id = recipient
            self._recipient = None
        else:
            if recipient.bot:
                raise CommandError("Recipient cannot be a bot.")
            self._id = recipient.id
            self._recipient = recipient
        self._other_recipients = other_recipients or []
        self._channel = channel
        self._genesis_message = None
        self._ready_event = asyncio.Event()
        self.wait_tasks = []
        self.close_task = None
        self.auto_close_task = None
        self._cancelled = False

    def __repr__(self):
        return f'Thread(recipient="{self.recipient or self.id}", channel={self.channel.id}, other_recipients={len(self._other_recipients)})'

    def __eq__(self, other):
        if isinstance(other, Thread):
            return self.id == other.id
        return super().__eq__(other)

    async def wait_until_ready(self) -> None:
        """Blocks execution until the thread is fully set up."""
        # timeout after 30 seconds
        task = self.bot.loop.create_task(asyncio.wait_for(self._ready_event.wait(), timeout=25))
        self.wait_tasks.append(task)
        try:
            await task
        except asyncio.TimeoutError:
            pass

        self.wait_tasks.remove(task)



class ModMail(Cog):

    def __init__(self, bot: Bot):
        self.modmail_forum_id = 1118969274527133808
        self.unresolved_tag_id = 1137631873288376471
        self.resolved_tag_id = 1134868441992527892
        self.bot = bot



def setup(bot: Bot) -> None:
    bot.add_cog(DialogStart(bot))
    print(f" + {__name__}")

def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
