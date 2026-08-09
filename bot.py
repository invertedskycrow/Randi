import asyncio
import random
import re
import discord
from discord import app_commands
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

ALLOWED_USER_IDS = {
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
}


def is_allowed(interaction: discord.Interaction) -> bool:
    return interaction.user.id in ALLOWED_USER_IDS


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
        self.view_ref.message = new_message
        await interaction.response.send_message(
            "Updated", ephemeral=True
        )


URL_RE = re.compile(r"https?://\S+")
IMAGE_EXTS = (".gif", ".png", ".jpg", ".jpeg", ".webp", ".mp4")
IMAGE_HOSTS = (
    "media.discordapp.net",
    "cdn.discordapp.com",
)


def find_image_url(text: str) -> str | None:
    match = URL_RE.search(text)
    if not match:
        return None
    url = match.group(0).rstrip(").,!?>\"'")
    path = url.split("?", 1)[0].lower()
    if path.endswith(IMAGE_EXTS) or any(host in path for host in IMAGE_HOSTS):
        return url
    return None


def bust_gif_cache(url: str) -> str:
    path = url.split("?", 1)[0].lower()
    if not path.endswith(".gif"):
        return url
    sep = "&" if "?" in url else "?"
    dummy = random.randint(100000, 999999)
    return f"{url}{sep}_cb={dummy}"


class RepeatView(discord.ui.View):
    def __init__(self, message: str):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔹", label="Send")
    async def send_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.message.strip():
            await interaction.response.send_message(
                "Use edit to set your message first",
                ephemeral=True,
            )
            return

        embed = discord.Embed(color=discord.Color.blurple())
        image_url = find_image_url(self.message)

        if image_url:
            embed.set_image(url=bust_gif_cache(image_url))
            remaining_text = self.message.replace(image_url, "").strip()
            if remaining_text:
                embed.description = remaining_text
        else:
            embed.description = self.message

        await interaction.response.send_message(embed=embed)

        # Send a fresh copy of the view right after, so it's at the bottom
        # of the channel instead of wherever the original command message is.
        await interaction.followup.send(
            "",
            view=RepeatView(self.message),
            ephemeral=True,
        )

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="⬛", label="Edit")
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditMessageModal(self))


@client.tree.command(name="_", description="randian tech")
@app_commands.describe(message="Optional starting message")
@app_commands.check(is_allowed)
async def say(interaction: discord.Interaction, message: str = ""):
    await interaction.response.send_message(
        "", view=RepeatView(message), ephemeral=True
    )


client.run(os.getenv("TOKEN"))
