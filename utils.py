from discord.ext import menus


class YesNoMenu(menus.Menu):

    def __init__(self, init_msg: str, embed=None):
        super().__init__(timeout=30.0)
        self.msg = init_msg
        self.result = None
        self.embed = embed

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.msg, embed=self.embed)

    @menus.button('\N{WHITE HEAVY CHECK MARK}')
    async def yes(self, payload):
        self.result = True
        await self.clear_buttons(react=True)
        self.stop()

    @menus.button('\N{CROSS MARK}')
    async def no(self, payload):
        self.result = False
        await self.clear_buttons(react=True)
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result, self.message
