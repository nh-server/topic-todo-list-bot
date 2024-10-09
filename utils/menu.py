import discord


class YesNoView(discord.ui.View):
    def __init__(self, interaction):
        self.interaction = interaction
        self.bot = interaction.client
        self.result = None
        super().__init__(timeout=60)

    async def on_error(self, interaction, exc, item):
        self.stop()

    async def on_timeout(self):
        self.stop()

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = False
        self.stop()
