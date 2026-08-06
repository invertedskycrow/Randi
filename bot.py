import asyncio
import discord
from discord import app_commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = MyClient()


class EditMessageModal(discord.ui.Modal, title="Edit"):
    def __init__(self, view: "RepeatView"):
        super().__init__()
        self.view_ref = view
        self.text_input = discord.ui.TextInput(
            label="Message",
            style=discord.TextStyle.paragraph,
            default=view.message,
            max_length=2000,
        )
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_message = self.text_input.value
        self.view_ref.message = self.text_input.value
        await interaction.response.send_message(
            "Updated", ephemeral=True
        )


class RepeatView(discord.ui.View):
    def __init__(self, message: str):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔹", label="Send")
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.message)

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⬛", label="Edit")
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditMessageModal(self))


@client.tree.command(name="say", description="randian tech")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(
        "", view=RepeatView(message), ephemeral=True
    )

client.run("TOKEN") #just copy and paste it here don't worry about environment variables