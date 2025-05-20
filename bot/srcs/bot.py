import discord
from discord.ext import commands
from srcs.db import db

intents = discord.Intents.all()
intents.message_content = True  # Nécessaire pour lire le contenu des messages
intents.members = True


bot = commands.Bot(command_prefix='!', intents=intents)

