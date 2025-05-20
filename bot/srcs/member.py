from srcs.db import Base, db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from srcs.bot import bot
from srcs.utils import change_user_name
import discord

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True)
    discord_id = Column(String, unique=True)
    name = Column(String)
    elo = Column(Integer, default=1000)
    

    matches_won = relationship('Match', back_populates='winner', foreign_keys='Match.winner_id')
    matches_lost = relationship('Match', back_populates='looser', foreign_keys='Match.looser_id')



    @staticmethod
    async def join(member):
        user_was_here = db.query(Member).filter(Member.discord_id == str(member.id)).first()
        if user_was_here:
            await Member.refresh_name(member)
            return
        new_user = Member(name=member.name, discord_id=str(member.id))
        db.add(new_user)
        db.commit()
        await Member.refresh_name(member)
        
    @staticmethod
    async def refresh_name(member):
        user = db.query(Member).filter(Member.discord_id == str(member.id)).first()
        await change_user_name(member, user.name + f" ({user.elo})")

        
    def __str__(self):
        return f"{self.name} ({self.discord_id})"

@bot.command()
async def stats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    user = db.query(Member).filter(Member.discord_id == str(member.id)).first()
    
    if user is None:
        await ctx.send("User not found in the database.")
        return
    
    await ctx.send(f"{member.name} has an Elo rating of {user.elo}. with {len(user.matches_won)} matches won and {len(user.matches_lost)} matches lost.")
    
@bot.event
async def on_member_join(member):
    await Member.join(member)
    


@bot.command()
async def username(ctx, new_name: str):

    member = ctx.author
    user = db.query(Member).filter(Member.discord_id == str(member.id)).first()
    if user is None:
        await ctx.send("User not found in the database.")
        return

    user.name = new_name
    db.commit()
    await Member.refresh_name(member)
    await ctx.send(f"Username changed from {member.name} to {new_name}.")