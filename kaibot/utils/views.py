import discord
from .translations import CONFIRM


class Confirm(discord.ui.View):
    def __init__(self, member, *, timeout=180):
        super().__init__(timeout=timeout)
        self.member = member
        self.value = None

        # Since we can't get the context in the decorator, we have to
        # define the label here.
        for child in self.children:
            if child.style == discord.ButtonStyle.green:
                child.label = CONFIRM['yes']
            else:
                child.label = CONFIRM['no']

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.member

    @discord.ui.button(style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
