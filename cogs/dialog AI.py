import dialogflow
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

        await channel.trigger_typing()

        DIALOGFLOW_PROJECT_ID = 'breadix-support-xyev'
        DIALOGFLOW_LANGUAGE_CODE = 'ru-RU'
        # GOOGLE_APPLICATION_CREDENTIALS = '1234567abcdef.json'
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

        print("Query text:" + str(response.query_result.query_text))
        print("Detected intent:" + response.query_result.intent.display_name)
        print("Detected intent confidence:" + str(response.query_result.intent_detection_confidence))
        print("Fulfillment text: " + response.query_result.fulfillment_text)
        if response.query_result.fulfillment_text != "":
            await message.reply(response.query_result.fulfillment_text)
        else:
            await message.reply("```Нет ответа```")

def setup(bot: Bot) -> None:
    bot.add_cog(AIHelper(bot))
    print(f" + {__name__}")


def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
