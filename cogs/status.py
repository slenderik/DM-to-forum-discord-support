from disnake import Activity, ActivityType
from disnake.ext import tasks, commands


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.status_loop.start()

    @tasks.loop(minutes=10.0)
    async def status_loop(self):
        activity = Activity(name="вас, пишите в лс", type=ActivityType.listening)
        await self.bot.change_presence(activity=activity)

    @status_loop.before_loop
    async def before_status_loop(self):
        await self.bot.wait_until_ready()
        print('[Status] Ready')


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Status(bot))
    print(f" + {__name__}")


def teardown(bot: commands.Bot) -> None:
    print(f" – {__name__}")
