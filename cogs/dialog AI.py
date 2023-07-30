import dialogflow
from disnake import Embed
from google.api_core.exceptions import InvalidArgument
from os import environ

import disnake
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog


class AIHelper(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} | {__name__}")

    @commands.Cog.listener("on_message")
    async def on_message_in_forum(self, message: disnake.Message):
        """FROM DM -> FORUM"""
        channel = message.channel

        if channel.id != 1133229583131488347:
            return

        if message.author.bot:
            return

        if message.content == "":
            return

        await channel.trigger_typing()

        DIALOGFLOW_PROJECT_ID = 'breadix-support-xyev'
        DIALOGFLOW_LANGUAGE_CODE = 'ru-RU'
        SESSION_ID = message.author.id

        text_to_be_analyzed = message.content

        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)

        text_input = dialogflow.types.TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
        query_input = dialogflow.types.QueryInput(text=text_input)

        try:
            response = session_client.detect_intent(session=session, query_input=query_input)
        except InvalidArgument:
            raise

        if response.query_result.fulfillment_text == "":
            await message.reply("Очень странно, но нет ответа.")
            return

        name = response.query_result.intent.display_name
        confidence = round(response.query_result.intent_detection_confidence, 1) * 100


        # TODO tag for intent

        embed = Embed(description=response.query_result.fulfillment_text)
        embed.set_author(name="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
        await message.reply(content=f"Я уверен что это {name} на {confidence}%", embed=embed)


def setup(bot: Bot) -> None:
    bot.add_cog(AIHelper(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
