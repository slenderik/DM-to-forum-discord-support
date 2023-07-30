import calendar
import datetime

from disnake import Message, DMChannel, HTTPException, Thread, User, \
    Member, Embed
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog

modmail_forum_id: int = 1118969274527133808


class DialogStart(Cog):

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

    # TODO execute command in DM
    # TODO typing event  \\ ai is alright
    # TODO add reactions!
    # TODO pin messages!!
    # TODO close for reaction and tag

    @commands.Cog.listener("on_message")
    async def delete_pin_message(self, message: Message):

        if not isinstance(message.channel, Thread):
            return

        if not message.channel.parent_id == modmail_forum_id:
            return

        if "pinned" in message.system_content:
            try:
                await message.delete()
            except Exception as e:
                print(e)

    @commands.Cog.listener("on_message")
    async def from_dm_to_forum(self, dm_message: Message):
        """DM -> FORUM"""

        user = dm_message.author

        # only direct message
        if not isinstance(dm_message.channel, DMChannel):
            return

        # only users
        if user.bot:
            return

        # get or create a thread
        thread = await self.get_modmail_thread(user)
        modmail_forum = self.bot.get_channel(modmail_forum_id)

        if modmail_forum is None:
            raise LookupError

        # creating new thread
        if thread is None:
            member = modmail_forum.guild.get_member(user.id)
            member = member.joined_at if member is not None else "нет"

            messages = 0
            async for message in dm_message.channel.history(limit=None):
                if not message.author.bot:
                    messages += 1

            threads = 0
            async for thread in modmail_forum.archived_threads():
                if str(user.id) in thread.name:
                    threads += 1

            timestamp = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

            text = f"**Создан:** <t:{timestamp}:R> \n \n" \
                   f"**Зашёл:** {member} \n" \
                   f"**Cообщений:** {messages} \n" \
                   f"**Обращений:** {threads}"
            embed = Embed(title="📫 Новое обращение", description=text)
            embed.set_author(name=f"<@{user.id}> ({user.id})", icon_url=user.display_avatar.url)
            # TODO доделать это..

            thread, thread_message = await modmail_forum.create_thread(name=f"{user.name} ({user.id})", embed=embed)
            await thread_message.pin()

        files = []
        for attachment in dm_message.attachments:
            files += await attachment.to_file(description=f"From {user.name} ({user.id})")

        webhooks = await modmail_forum.webhooks()

        if not webhooks:
            webhook = await modmail_forum.create_webhook(name="Support hook", reason="Modmail")
        else:
            webhook = webhooks[0]

        try:
            # TODO stickers=dm_message.stickers,
            await webhook.send(
                content=dm_message.content,
                username=user.name,
                avatar_url=user.display_avatar.url,
                embeds=dm_message.embeds,
                files=files,
                components=dm_message.components,
                thread=thread
            )
        except Exception as e:
            await dm_message.add_reaction("⚠️")
            # TODO нормальная обработка ошибок // текст
            await dm_message.channel.send("⚠️ Похоже произошла ошибка. Пожалуйста, попробуйте обратится позже.")
            await thread.send(f"ERROR: `{e}`")
            print(f"ERROR: {e}")
        else:
            await dm_message.add_reaction("✔️")

            skip_once = True
            # clear previous messages
            async for message in dm_message.channel.history(limit=20):
                if skip_once is True:
                    skip_once = False
                    continue

                await message.remove_reaction("✔️", self.bot.user)

    @commands.Cog.listener("on_message")
    async def from_forum_to_dm(self, message: Message):
        """FORUM -> DM"""

        if not message.webhook_id is None:
            return

        if message.author.id == self.bot.user.id:
            return

        if not isinstance(message.channel, Thread):
            return

        if not message.channel.parent_id == modmail_forum_id:
            return

        thread = message.channel
        user_id = thread.name[-19:-1]

        try:
            user = await self.bot.get_or_fetch_user(user_id)
        except HTTPException:
            print()

        # send a message
        try:
            files = []
            for attachment in message.attachments:
                files += await attachment.to_file(description=f"From {user.name} ({user.id})")

            await user.send(files=files, embeds=message.embeds, content=message.content, stickers=message.stickers,
                            components=message.components)
        except Exception as e:
            await message.add_reaction("⚠️")
            await thread.send(f"```{e}``` User id -> {user_id}")
        else:
            await message.add_reaction("✔️")


def setup(bot: Bot) -> None:
    bot.add_cog(DialogStart(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
