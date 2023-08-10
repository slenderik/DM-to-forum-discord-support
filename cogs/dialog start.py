import calendar
from time import time, mktime

from disnake import Message, DMChannel, HTTPException, Thread, User, \
    Member, Embed, ForumTag, ForumChannel
from disnake.abc import GuildChannel
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog

modmail_forum_id: int = 1118969274527133808
id_unresolved_tag: int = 1137631873288376471
id_resolved_tag: int = 1134868441992527892


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

    @commands.Cog.listener("on_thread_update")
    async def close_forum_with_tag(self, before: Thread, after: Thread):
        """Archives the branch, when adding the tag Solved the problem"""

        if after is None:
            return

        if after.parent.id != modmail_forum_id:
            return

        forum: ForumChannel = before.parent
        tag = forum.get_tag(id_resolved_tag)

        print(tag not in before.applied_tags and tag in after.applied_tags)
        # TODO не работает

        if tag not in before.applied_tags and tag in after.applied_tags:
            await after.edit(archived=True)

    @commands.Cog.listener("on_thread_update")
    async def delete_unresolved_tag_from_resolved(self, before: Thread, after: Thread):

        if after is None:
            return

        if after.parent.id != modmail_forum_id:
            return

        forum: ForumChannel = before.parent
        tag = forum.get_tag(id_resolved_tag)

        if tag not in before.applied_tags and tag in after.applied_tags:
            try:
                tags = forum.available_tags
                unresolved_tag = forum.get_tag(id_unresolved_tag)
                tags.remove(unresolved_tag)
                await after.edit(applied_tags=tags)
            except:
                pass

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
        start_time = time()
        print(f"--- check start {time() - start_time} ---")
        user: User = dm_message.author

        # only direct message
        if not isinstance(dm_message.channel, DMChannel):
            return

        # only users
        if user.bot:
            return

        print(f"--- check end {time() - start_time} ---")

        # get or create a thread
        thread: Thread = await self.get_modmail_thread(user)
        forum: ForumChannel = self.bot.get_channel(modmail_forum_id)

        # creating new thread
        if thread is None:

            print(f"--- 1 create thread {time() - start_time} ---")
            # get number of messages form author
            messages = 0
            async for message in dm_message.channel.history(limit=None):
                if not message.author.bot:
                    messages += 1

            # get number of threads from author
            threads = 0
            async for thread in forum.archived_threads():
                if str(user.id) in thread.name:
                    threads += 1

            member = forum.guild.get_member(user.id)
            member = "нет" if member is None else round(mktime(member.joined_at.timetuple()))
            timestamp = round(time())

            print(f"--- 2 create thread {time() - start_time} ---")

            text = f"**Создан:** <t:{timestamp}:R> \n \n" \
                   f"**Зашёл:** {member} \n" \
                   f"**Cообщений:** {messages} \n" \
                   f"**Обращений:** {threads}"

            embed = Embed(title="📫 Новое обращение", description=text)
            embed.set_thumbnail(url=user.display_avatar.url)

            # add unresolved tag
            tags = forum.available_tags
            unresolved_tag = forum.get_tag(id_unresolved_tag)
            tags.append(unresolved_tag)

            thread, thread_message = await forum.create_thread(
                name=f"{user.name} ({user.id})",
                embed=embed, applied_tags=tags
            )
            await thread_message.pin()

            print(f"--- 3 create thread {time() - start_time} ---")

        # TODO add conversation tag
        # name = response.query_result.intent.display_name
        # add or create new tag about thread theme
        # tags = forum.available_tags
        # tags.append(ForumTag(name=""))
        # await forum.edit(available_tags=tags)

        # send a message
        files = []
        for attachment in dm_message.attachments:
            files += await attachment.to_file(description=f"From {user.name} ({user.id})")

        # webhooks = await forum.webhooks()
        #
        # if not webhooks:
        #     webhook = await forum.create_webhook(name="Support hook", reason="Modmail")
        # else:
        #     webhook = webhooks[0]

        try:
            await thread.send(
                stickers=dm_message.stickers,
                content=dm_message.content,
                embeds=dm_message.embeds,
                files=files,
                components=dm_message.components
            )

            print(f"--- send on {time() - start_time} ---")

        except Exception as e:
            await dm_message.add_reaction("⚠️")
            # TODO нормальная обработка ошибок // текст
            await dm_message.channel.send("⚠️ Похоже произошла ошибка. Пожалуйста, попробуйте обратится позже.")
            await thread.send(f"ERROR: `{e}`")
            print(f"ERROR: {e}")
        else:
            await dm_message.add_reaction("✔️")

            print(f"--- start delete marks {time() - start_time} ---")

            skip_once = True
            # clear previous messages
            async for message in dm_message.channel.history(limit=2):
                if skip_once is True:
                    skip_once = False
                    continue

                await message.remove_reaction("✔️", self.bot.user)
            print(f"--- end delete marks {time() - start_time} ---")

        print(f"--- end {time() - start_time} ---")

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
