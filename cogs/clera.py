from os import environ

import disnake
from disnake import Message, Embed
from disnake.ext import commands
from disnake.ext.commands import Bot, Cog

class DMChannel:
    """Represent a DM channel, user info and dialog status """

    def __init__(
        self,
        dm_channel = [disnake.DMChannel],
        message = [disnake.Message]
    ):
        self.dm_channel = dm_channel
        self.channel_id = None

        self.last_message_id = None




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


async def get_formated_message(message: Message):
    """Formated simple message, for format to send. Embed + files, stickers"""

    user = message.author

    files = []

    for file in message.attachments:
        text = f"От {user.display_name} ({user.id}) в поддержку."
        await file.to_file(description=text)

    files = []
    for attachment in message.attachments:
        files += await attachment.to_file(description=f"От {user.display_name} ({user.id}) в поддержку.")

    embed = Embed()

    embed.set_footer(text=)



class ModMail(Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def dm2thread(self, message: Message):
        """Send message from DM to modmail thread. If it needs to create one."""

        if not isinstance(message.channel, disnake.DMChannel):
            return

        if message.author.bot or message.webhook_id:
            return




        # photo or video
        if message.attachments and message.content == "":


            embed = Embed(description="Чтобы быстрее ответить – опишите то, что находится на изображении.")
            embed.set_footer(text="Ассистент Хлеб Хлебович", icon_url=self.bot.user.display_avatar.url)
            return











def setup(bot: Bot) -> None:
    bot.add_cog(ModMail(bot))
    print(f" + {__name__}")

def teardown(bot: Bot) -> None:
    print(f" – {__name__}")
