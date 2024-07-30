from flask import Flask, render_template
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return '''<body style="margin: 0; padding: 0;">
    <iframe width="100%" height="100%" src="https://axocoder.vercel.app/" frameborder="0" allowfullscreen></iframe>
  </body>'''

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():  
    t = Thread(target=run)
    t.start()

keep_alive()
print("Server Running Because of Axo")




import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of packages to ensure are installed
required_packages = [
    'discord.py'
]

# Install any missing packages
for package in required_packages:
    try:
        __import__(package.split('==')[0])
    except ImportError:
        print(f'{package} not found. Installing...')
        install(package)

# Continue with the rest of your bot code
import discord
from discord.ext import commands
import random
import string
import json
import asyncio

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['TOKEN']
GUILD_ID = config['GUILD_ID']
WHITELIST_ROLE_ID = config['WHITELIST_ROLE_ID']
VERIFY_CHANNEL_ID = config['VERIFY_CHANNEL_ID']

# Set up intents
intents = discord.Intents.default()
intents.members = True  # Enable the members intent
intents.messages = True  # Enable the message content intent
intents.message_content = True  # Enable the message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

# Store verification codes
user_verification_codes = {}

# Custom help command class
class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={'help': 'Shows this help message'})

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Command List",
            description=(
                "`!start` - Sends a message to a specific channel to start the verification process.\n"
                "`!help` - Displays this help message."
            ),
            color=discord.Color.blue()
        )
        await self.get_destination().send(embed=embed)

bot.help_command = CustomHelpCommand()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='start')
async def start(ctx):
    channel = bot.get_channel(int(VERIFY_CHANNEL_ID))
    if channel:
        embed = discord.Embed(
            title="Verification",
            description="React with ✅ to receive a verification code via DM!",
            color=discord.Color.blue()
        )
        message = await channel.send(embed=embed)
        await message.add_reaction('✅')
        await ctx.send(embed=discord.Embed(
            description=f'The verification message has been sent to {channel.mention}.',
            color=discord.Color.green()
        ))
    else:
        await ctx.send(embed=discord.Embed(
            description='The verification channel could not be found.',
            color=discord.Color.red()
        ))

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == '✅' and not user.bot:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        try:
            await user.send(embed=discord.Embed(
                title="Verification Code",
                description=f'Your verification code is: **{code}**',
                color=discord.Color.orange()
            ))
            user_verification_codes[user.id] = code
        except discord.Forbidden:
            print(f'Could not send DM to {user.name}.')
            await reaction.message.channel.send(embed=discord.Embed(
                description=f'Could not send DM to {user.name}. Please make sure you have DMs enabled.',
                color=discord.Color.red()
            ))

        ack_message = await reaction.message.channel.send(embed=discord.Embed(
            title="Verification Sent",
            description=f'{user.name}, a verification code has been sent to your DMs!',
            color=discord.Color.green()
        ))
        await asyncio.sleep(60)
        try:
            await ack_message.delete()
        except discord.Forbidden:
            print(f'Could not delete message sent to {user.name}.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id in user_verification_codes:
        if message.content == user_verification_codes[message.author.id]:
            guild = discord.utils.get(bot.guilds, id=int(GUILD_ID))
            if guild:
                role = discord.utils.get(guild.roles, id=int(WHITELIST_ROLE_ID))
                if role:
                    member = guild.get_member(message.author.id)
                    if member:
                        if discord.utils.get(guild.me.roles, id=role.id):
                            try:
                                await member.add_roles(role)
                                await message.channel.send(embed=discord.Embed(
                                    description='You are verified and have been given the whitelist role!',
                                    color=discord.Color.green()
                                ))
                            except discord.Forbidden:
                                await message.channel.send(embed=discord.Embed(
                                    description='I do not have permission to assign the role. Please contact an admin.',
                                    color=discord.Color.red()
                                ))
                        else:
                            await message.channel.send(embed=discord.Embed(
                                description='Bot does not have the necessary permissions to assign roles.',
                                color=discord.Color.red()
                            ))
                    else:
                        await message.channel.send(embed=discord.Embed(
                            description='Failed to find the member in the guild. Please contact an admin.',
                            color=discord.Color.red()
                        ))
                else:
                    await message.channel.send(embed=discord.Embed(
                        description='Whitelist role not found. Please contact an admin.',
                        color=discord.Color.red()
                    ))
            else:
                await message.channel.send(embed=discord.Embed(
                    description='Guild not found. Please contact an admin.',
                    color=discord.Color.red()
                ))

            del user_verification_codes[message.author.id]
        else:
            await message.channel.send(embed=discord.Embed(
                description='Wrong code. Please try again.',
                color=discord.Color.red()
            ))

    await bot.process_commands(message)

bot.run(TOKEN)
