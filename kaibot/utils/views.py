import discord
from .translations import CONFIRM
from .enums import Emotes


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


class PaginatorView(discord.ui.View):
    def __init__(self, *, message, timeout=180):
        self.message = message
        self.current_page = 0
        super().__init__(timeout=timeout)

    async def show_current_page(self):
        raise NotImplementedError()

    def get_max_pages(self):
        raise NotImplementedError

    @discord.ui.button(emoji=Emotes.FIRST, style=discord.ButtonStyle.blurple)
    async def go_to_first(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = 0
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.PREVIOUS, style=discord.ButtonStyle.blurple)
    async def go_to_previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page -= 1
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.STOP, style=discord.ButtonStyle.red)
    async def stop_paginator(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.message.edit(view=None)

        self.stop()

    async def on_timeout(self):
        await self.message.edit(view=None)

    @discord.ui.button(emoji=Emotes.NEXT, style=discord.ButtonStyle.blurple)
    async def go_to_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page += 1
        await self.show_current_page()

    @discord.ui.button(emoji=Emotes.LAST, style=discord.ButtonStyle.blurple)
    async def go_to_last(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = self.get_max_pages() - 1
        await self.show_current_page()
