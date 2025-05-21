import discord
from discord.ext import commands
from srcs.db import db
from srcs.member import Member
from srcs.match import Match
from srcs.bot import bot

@bot.command()
async def refresh(ctx):
    for member in ctx.guild.members:
        user_exist = db.query(Member).filter(Member.discord_id == str(member.id)).first()
        if user_exist:
            continue
        new_user = Member(name=member.name, discord_id=str(member.id))
        db.add(new_user)
        db.commit() 

    for member in ctx.guild.members:
        await Member.refresh_name(member)
        # await reset_name(member)
    await ctx.send("Member refreshing completed.")
        
@bot.command()
async def scoreboard(ctx, ammount: int = 20):
    subquery = db.query(Match.winner_id).union(
        db.query(Match.looser_id)
    ).subquery()
    members = db.query(Member).filter(Member.id.in_(subquery)).order_by(Member.elo.desc()).all()
    embed = discord.Embed(title="Scoreboard", color=discord.Color.blue())
    
    i = 0
    for member in members:
        embed.add_field(name=f"{i + 1}.{member.name}", value=f"Elo: {member.elo}", inline=False)
        i += 1
        if i >= ammount or i >= 20:
            break
    
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
