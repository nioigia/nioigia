
from ast import Interactive
from ctypes import Union
import discord
from discord import Intents, app_commands, Embed
import json
import os

# Load saved reactions from a JSON file
try:
    with open("reactions.json", "r") as file:
        reactions = json.load(file)
except FileNotFoundError:
    reactions = {}

try:
    with open("message_responses.json", "r") as file:
        message_responses = json.load(file)
except FileNotFoundError:
    message_responses = {}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


@tree.command(name="hello", description="Sends a friendly greeting! :3")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello there! Nice to meet you! ")

@tree.command(name="send", description="Sends a message multiple times in a chosen channel! ^^")
async def send(interaction: discord.Interaction, channel: discord.TextChannel, message: str, count: int):
    if count < 1:
        await interaction.response.send_message("Number of messages must be at least 1! ")
        return

    channel = await interaction.guild.fetch_channel(channel.id)

    # Send messages and confirmation immediately
    for _ in range(count):
        await channel.send(message)

    await interaction.response.send_message(f"Sent **{count}** messages in #{channel.name}! ")  # Send confirmation immediately

@tree.command(name="auto_reaction", description="Sets an emoji to react to a specific message")
async def auto_reaction(interaction: discord.Interaction, message: str, emoji: str, wildcard: bool = False):
    reactions[message.lower()] = {"emoji": emoji, "wildcard": wildcard}
    await interaction.response.send_message(f"Auto reaction set for '{message}' with emoji '{emoji}' and wildcard {wildcard}")

    # Save reactions to the JSON file
    with open("reactions.json", "w") as file:
        json.dump(reactions, file)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    for saved_message, reaction_data in reactions.items():
        if reaction_data["wildcard"]:
            if saved_message in message.content.lower():
                await message.add_reaction(reaction_data["emoji"])
        else:
            if message.content.lower() == saved_message:
                await message.add_reaction(reaction_data["emoji"])


@tree.command(name="auto_message", description="Sets a message to send for a specific message")
async def auto_message(interaction: discord.Interaction, message: str, response: str, wildcard: bool = False):
    message_responses[message.lower()] = {"response": response, "wildcard": wildcard}
    await interaction.response.send_message(f"Auto message set for '{message}' with response '{response}' and wildcard {wildcard}")

    # Save message-response pairs to the JSON file
    with open("message_responses.json", "w") as file:
        json.dump(message_responses, file)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    for saved_message, response_data in message_responses.items():
        if response_data["wildcard"]:
            if saved_message in message.content.lower():
                await message.channel.send(response_data["response"])
        else:
            if message.content.lower() == saved_message:
                await message.channel.send(response_data["response"])

@tree.command(name="mute", description="Mutes a member in the server")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str = "0s", reason: str = "No reason specified"):
    try:
        guild = interaction.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")  # Replace "Muted" with your actual muted role name

        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.text_channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)

        # Immediate response after muting
        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"{member.mention} has been muted for {duration}. Reason: {reason}")

        try:
            await member.send(f"You have been muted in {interaction.guild.name} for {duration}. Reason: {reason}")
        except discord.Forbidden:
            await interaction.followup.send(f"Unable to send a DM to {member.mention} to inform them of the mute.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have the permissions to manage roles.")

@tree.command(name="unmute", description="Unmutes a muted member in the server")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    try:
        guild = interaction.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")  # Replace "Muted" with your actual muted role name

        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            await interaction.response.send_message(f"{member.mention} has been unmuted.")
            try:
                await member.send(f"You have been unmuted in {interaction.guild.name}.")
            except discord.Forbidden:
                await interaction.followup.send(f"Unable to send a DM to {member.mention} to inform them of the unmute.")
        else:
            await interaction.response.send_message(f"{member.mention} is not muted.")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have the permissions to manage roles.")

@tree.command(name="custom_embed", description="Create and edit custom embeds")
async def custom_embed(interaction: discord.Interaction,
    embed_name: str,
    title: str = None,
    author: str = None,
    author_link: str = None,
    author_avatar: str = None,
    description: str = None,
    image_url: str = None,
    thumbnail_url: str = None,
    footer: str = None,
    footer_icon: str = None,
    color: str = None,
    timestamp: bool = True,
):
    # Load or create JSON file for saved embeds
    embed_file = f"embeds/{embed_name}.json"
    try:
        with open(embed_file, "r") as f:
            embed_data = json.load(f)
    except FileNotFoundError:
        embed_data = {}

    # Update embed data based on provided arguments
    if title:
        embed_data["title"] = title
    if author:
        embed_data["author"] = {"name": author}
        if author_link:
            embed_data["author"]["url"] = author_link
        if author_avatar:
            embed_data["author"]["icon_url"] = author_avatar
    if description:
        embed_data["description"] = description
    if image_url:
        embed_data["image"] = {"url": image_url}
    if thumbnail_url:
        embed_data["thumbnail"] = {"url": thumbnail_url}
    if footer:
        embed_data["footer"] = {"text": footer}
        if footer_icon:
            embed_data["footer"]["icon_url"] = footer_icon
    if color:
        if color.startswith("#"):
            # Hex code
            embed_data["color"] = int(color[1:], 16)
        else:
            # Color name
            try:
                embed_data["color"] = getattr(discord.Color, color.lower())
            except AttributeError:
                await interaction.response.send_message(f"Invalid color name: {color}")
                return

    # Create embed object from data
    embed = Embed()
    for key, value in embed_data.items():
        if key == "image":
            embed.set_image(url=value["url"])
        elif key == "thumbnail":
            embed.set_thumbnail(url=value["url"])
        elif key == "color":
            embed.colour = value
        elif key == "footer":
            embed.set_footer(text=value["text"], icon_url=value.get("icon_url"))
        else:
            setattr(embed, key, value)

    # Send embed based on message context
    channel = interaction.channel
    if (interaction.is_command_context() and interaction.guild):
        # Command usage
        await interaction.response.send_message(embed=embed)
    elif interaction.is_message_context():
        # Reply to message
        await interaction.message.reply(embed=embed)
    elif interaction.is_user_context():
        # DM the user
        if interaction.target:
            try:
                await interaction.target.send(embed=embed)
            except discord.HTTPException:
                await interaction.response.send_message(f"Unable to DM user: {interaction.target}")
        else:
            await interaction.response.send_message(f"Cannot DM in this context")

    # Save updated embed data to JSON
    with open(embed_file, "w") as f:
        json.dump(embed_data, f)

    # Optional welcome message setting
    # ... (implement logic to link the command to welcome messages based on your chosen approach)

    # Optional leave message setting
    # ... (implement logic to link the command to leave messages based on your chosen approach)

    # Optional boost message setting
    # ... (implement logic to link the command to boost messages based on your chosen approach)

    await interaction.response.send_message(f"Embed '{embed_name}' updated successfully!")

client.run("MTIwMDY5NjM4ODA3NDM2MDg2Mw.GkM0oR.RlbX-uCfVXSzP3VTkNoiEiii72ZvkPLNKuP_Uk")  # Replace with your bot token