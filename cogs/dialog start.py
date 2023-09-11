from time import time, mktime
from cogs.AI import ai_answer

from disnake import Message, DMChannel, HTTPException, Thread, User, \
    Member, Embed, ForumChannel
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog

modmail_forum_id: int = 1118969274527133808
unresolved_tag_id: int = 1137631873288376471
resolved_tag_id: int = 1134868441992527892


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

    async def call_agent(self, thread: Thread, dm_message: Message):
        embed = Embed(description="**Ждём ответа.** Ответим в течении 24-х часов.")
        embed.set_footer(text="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
        await dm_message.reply(embed=embed)
        await thread.send("<@&1150512891804536913>, здесь нужна помощь. Бот не вывез!")

    # TODO try except else
    # TODO execute command in DM
    # TODO typing event  \\ ai is alright
    # TODO add reactions!
    # TODO pin messages!!
    # TODO close for reaction and tag
    # TODO add conversation tag
    # name = response.query_result.intent.display_name
    # add or create new tag about thread theme
    # tags = forum.available_tags
    # tags.append(ForumTag(name=""))
    # await forum.edit(available_tags=tags)

    @commands.Cog.listener("on_thread_update")
    async def close_forum_with_tag(self, before: Thread, after: Thread):
        """Archives the branch, when adding the tag Solved the problem"""

        if after is None:
            return

        if after.parent.id != modmail_forum_id:
            return

        forum: ForumChannel = before.parent
        tag = forum.get_tag(resolved_tag_id)

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
        tag = forum.get_tag(resolved_tag_id)

        if tag not in before.applied_tags and tag in after.applied_tags:
            try:
                tags = forum.available_tags
                unresolved_tag = forum.get_tag(unresolved_tag_id)
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

        print(f"- check {time() - start_time}")

        # only direct message
        if not isinstance(dm, DMChannel):
            return

        # only users
        if user.bot:
            return

        # get a thread
        thread: Thread = await self.get_modmail_thread(user)
        forum: ForumChannel = self.bot.get_channel(modmail_forum_id)

        # create new one
        if thread is None:
            print(f"- 1 create thread {time() - start_time}")

            # create embed
            member = forum.guild.get_member(user.id)
            join_time = "нет" if member is None else round(mktime(member.joined_at.timetuple()))

            embed = Embed(
                title="📫 Обращение",
                description=f"Создан: <t:{join_time}:R> \n Зашёл: {member}"
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            # add unresolved tag
            tags = forum.available_tags
            tags.append(forum.get_tag(unresolved_tag_id))

            thread, thread_message = await forum.create_thread(
                name=f"{user.name} ({user.id})",
                applied_tags=tags
            )
            await thread_message.pin()

        print(f"- message send {time() - start_time}")
        print("STICKERS: ", bool(dm_message.stickers), " - ", dm_message.stickers)
        print("ATTACHMENTS: ", bool(dm_message.attachments), " - ", dm_message.attachments)

        # photo or video
        if dm_message.attachments and dm_message.content == "":
            files = []
            for attachment in dm_message.attachments:
                files += await attachment.to_file(description=f"От {user.display_name} ({user.id}) в поддержку.")

            embed = Embed(description="Чтобы быстрее ответить – опишите то, что находится на изображении.")
            embed.set_footer(text="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
            await dm_message.reply(embed=embed)
            await thread.send(files=files)
            return

        # sticker only
        elif dm_message.stickers:
            text = f"От {user.display_name} ({user.id}) в поддержку."
            stickers = []
            for sticker in dm_message.stickers:
                stickers += self.bot.get_sticker(sticker.id)
                # stickers += await sticker.to_file(description=text)

            await self.call_agent(thread, dm_message)
            await thread.send(stickers=stickers)
            return

        #TODO system_content

        elif dm_message.content != "":

            # send message to thread
            text = f"От {user.display_name} ({user.id}) в поддержку."
            files = [await file.to_file(description=text) for file in dm_message.attachments]
            await thread.send(content=dm_message.content, files=files)

            # add reaction as answer about success
            # clear previous reaction
            async for message in dm_message.channel.history(after=dm_message.created_at, limit=2):
                if message.author.bot:
                    continue

                await message.remove_reaction("✔️", self.bot.user)
            # and add new one
            await dm_message.add_reaction("✔️")

            print(f"- AI start {time() - start_time}")

            # AI try to answer
            await dm.trigger_typing()
            await thread.trigger_typing()

            response = await ai_answer(dm_message.content, user.id)
            confidence = response.intent_detection_confidence
            name = response.intent.display_name
            answer = response.fulfillment_text

            # AI can't answer - call agent
            if answer == "Агент" or answer == "" or confidence <= 0.5:
                await self.call_agent(thread, dm_message)

            else:
                embed = Embed(description=answer)
                embed.set_footer(text="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
                await dm_message.reply(embed=embed)
                await thread.send(content=f"`{name} - {confidence}`", embed=embed)

            print(f"- AI answered {time() - start_time}")
            print(f"_______________ \n")

        else:
            print("THIS IS FUCK!")

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
