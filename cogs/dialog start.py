from time import time, mktime
from cogs.AI import AI_answer

from disnake import Message, DMChannel, HTTPException, Thread, User, \
    Member, Embed, ForumTag, ForumChannel
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
    async def support_dm2thread(self, dm_message: Message):

        start_time = time()
        user: User = dm_message.author
        dm: DMChannel = dm_message.channel

        # only direct message
        if not isinstance(dm, DMChannel):
            return

        # only users
        if user.bot:
            return

        print(f"- check {time() - start_time}")

        # get or create a thread
        thread: Thread = await self.get_modmail_thread(user)
        forum: ForumChannel = self.bot.get_channel(modmail_forum_id)

        # create new empty thread
        thread_message = None
        if thread is None:
            thread, thread_message = await forum.create_thread(name=f"{user.name} ({user.id})", content="Загрузка")
            print(f"- create thread {time() - start_time}")

        # send a message
        files = []
        for attachment in dm_message.attachments:
            files += await attachment.to_file(description=f"От {user.name} ({user.id}) в поддержку")

        try:
            await thread.send(
                stickers=dm_message.stickers,
                content=dm_message.content,
                embeds=dm_message.embeds,
                files=files,
                components=dm_message.components
            )
            print(f"- message send {time() - start_time}")
        except Exception as e:
            # TODO нормальная обработка ошибок // текст
            await dm_message.add_reaction("⚠️")
            await dm_message.channel.send("⚠️ Похоже произошла ошибка. Пожалуйста, попробуйте обратится позже.")
            await thread.send(f"ERROR: `{e}`")
            print(f"ERROR: {e}")
        else:
            # # clear previous reaction
            # skip_once = True
            # print(f"- delete marks {time() - start_time}")
            # async for message in dm_message.channel.history(limit=2):
            #     if message.author.bot:
            #         continue
            #
            #     if skip_once is True:
            #         skip_once = False
            #         continue
            #
            #     await message.remove_reaction("✔️", self.bot.user)

            # filling an empty branch with data
            await dm_message.add_reaction("✔️")
            print(f"- delete marks {time() - start_time}")

        # TODO add conversation tag
        # name = response.query_result.intent.display_name
        # add or create new tag about thread theme
        # tags = forum.available_tags
        # tags.append(ForumTag(name=""))
        # await forum.edit(available_tags=tags)

        # filling an empty thread with data
        if thread_message is not None:

            print(f"- 1 create thread {time() - start_time}")
            await thread_message.pin()

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

            print(f"- 2 create thread {time() - start_time}")

            text = f"**Создан:** <t:{timestamp}:R> \n \n" \
                   f"**Зашёл:** {member} \n" \
                   f"**Cообщений:** {messages} \n" \
                   f"**Обращений:** {threads}"

            embed = Embed(title="📫 Новое обращение", description=text)
            embed.set_thumbnail(url=user.display_avatar.url)

            await thread_message.edit(conntent=None, embed=embed)

            # add unresolved tag
            tags = forum.available_tags
            unresolved_tag = forum.get_tag(id_unresolved_tag)
            tags.append(unresolved_tag)

            await thread.edit(applied_tags=tags)

            print(f"- 3 create thread {time() - start_time}")

        print(f"- AI start {time() - start_time}")

        # AI try to answer
        if dm_message.content == "":
            return

        await dm.trigger_typing()

        response = await AI_answer(dm_message.content, user.id)

        if response.fulfillment_text == "":
            await dm_message.reply("Очень странно, нет ответа.")
            return

        name = response.intent.display_name
        confidence = round(response.intent_detection_confidence, 1) * 100

        embed = Embed(description=response.fulfillment_text)
        embed.set_footer(text="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
        await dm_message.reply(embed=embed)
        await thread.send(content=f"`{name} - {confidence}%`", embed=embed)

        print(f"- AI answered {time() - start_time}")

    @commands.Cog.listener("on_message")
    async def support_thread2dm(self, message: Message):
        start_time = time()
        if message.author.id == self.bot.user.id:
            return
        if not isinstance(message.channel, Thread):
            return
        if not message.channel.parent_id == modmail_forum_id:
            return

        print(f"- check {time() - start_time}")

        thread: Thread = message.channel
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

            print(f"- message send {time() - start_time}")
        except Exception as e:
            await message.add_reaction("⚠️")
            await thread.send(f"```{e}``` User id -> {user_id}")
        else:
            await message.add_reaction("✔️")
            print(f"- reaction {time() - start_time}")


def setup(bot: Bot) -> None:
    bot.add_cog(DialogStart(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
