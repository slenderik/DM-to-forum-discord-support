from google.cloud import dialogflow

from google.cloud.dialogflow import QueryResult
from disnake import Embed
from google.api_core.exceptions import InvalidArgument
from os import environ

# TODO migrate to google.cloud
import disnake
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog


async def ai_answer(text: str, session_id: int, context: str = None) -> QueryResult:
    project_id = environ.get("DIALOGFLOW_PROJECT_ID")
    language = 'ru-RU'

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language)
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
        return response.query_result

    except InvalidArgument:
        raise


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

        response = await ai_answer(message.content, message.author.id)

        if response.fulfillment_text == "":
            await message.reply("Очень странно, но нет ответа.")
            return

        name = response.intent.display_name
        confidence = round(response.intent_detection_confidence, 1) * 100

        embed = Embed(description=response.fulfillment_text)
        embed.set_author(name="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
        await message.reply(content=f"Уверен это {name} на {confidence}%", embed=embed)


def setup(bot: Bot) -> None:
    bot.add_cog(AIHelper(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
