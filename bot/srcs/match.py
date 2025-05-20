from srcs.db import Base, db
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from srcs.utils import change_user_name
from datetime import datetime
from srcs.member import Member
from srcs.elo import change_elo
from srcs.bot import bot
from discord.ext import commands
import discord
from sqlalchemy import or_

class Match(Base):
    __tablename__ = 'match'
    
    id = Column(Integer, primary_key=True)
    #link to the player1 and player2 with one to many relationship
    winner_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    looser_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    
    winner = relationship('Member', foreign_keys=[winner_id], back_populates='matches_won')
    looser = relationship('Member', foreign_keys=[looser_id], back_populates='matches_lost')
    
    date = Column(DateTime, default=datetime.now())
    
    score_winner = Column(Integer, nullable=False)
    score_looser = Column(Integer, nullable=False)

    winner_elo_before = Column(Integer, nullable=False)
    looser_elo_before = Column(Integer, nullable=False)
    
    winner_elo_after = Column(Integer, nullable=False)
    looser_elo_after = Column(Integer, nullable=False)

    @staticmethod
    async def save_match(winner, looser, score_winner, score_looser):
        
        winner_db = db.query(Member).filter(Member.discord_id == str(winner.id)).first()
        looser_db = db.query(Member).filter(Member.discord_id == str(looser.id)).first()
        
        winner_elo_before = winner_db.elo
        looser_elo_before = looser_db.elo
        
       
        
        set_amount = abs(score_winner - score_looser)
        k = 32
        if set_amount == 2:
            k += 12 * 1
        elif set_amount == 3:
            k += 12 * 2
        elif set_amount == 4:
            k += 12 * 3
        elif set_amount == 5:
            k += 12 * 4
        elif set_amount >= 6:
            k += 12 * 5
        
        winner_elo_after, looser_elo_after = await change_elo(winner, looser)



        new_match = Match(winner_id=winner_db.id,
                            looser_id=looser_db.id,
                            score_winner=score_winner,
                            score_looser=score_looser,
                            winner_elo_before=winner_elo_before,
                            looser_elo_before=looser_elo_before,
                            winner_elo_after=winner_elo_after,
                            looser_elo_after=looser_elo_after)
        
        db.add(new_match)
        db.commit()
        return new_match


@bot.command()
async def match(ctx, opponent: discord.Member, score: str):
    
    
    if ctx.channel.id != 1366331265464275004:
        await ctx.send("This command can only be used in the channel <#1366331265464275004>.")
        return
    
    
    # Parse the score (example: '11-2' -> (11, 2))
    try:
        player_score, opponent_score = map(int, score.split('-'))
    except ValueError:
        await ctx.send("Invalid score format. Please use the format 'X-Y'.")
        return

    # Display the message and ask for confirmation
    if player_score < 0 or opponent_score < 0:
        await ctx.send("Scores must be non-negative.")
        return

    if player_score == opponent_score:
        await ctx.send("Scores must be different. Ties are not taken into account.")
        return

    if player_score < opponent_score:
        msg = await ctx.send(f"{opponent.mention} do you confirm having beaten {ctx.author.mention} in a {max(player_score, opponent_score) * 2 - 1} sets match with a final score of {score}?\n\nReact with ✅ to confirm or ❌ to cancel.")
    else:
        msg = await ctx.send(f"{opponent.mention} do you confirm having lost to {ctx.author.mention} in a {max(player_score, opponent_score) * 2 - 1} sets match with a final score of {score}?\n\nReact with ✅ to confirm or ❌ to cancel.")
    
    # Add the reactions
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    # Wait for the reaction
    def check(reaction, user):
        return (user == opponent and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == msg.id) or (reaction.message.id == msg.id and user == ctx.author and str(reaction.emoji) == '❌')

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=15 * 60)
    except TimeoutError:
        await ctx.send(f"Sorry {ctx.author.mention}, {opponent.mention} did not respond in time. No changes were made.")
        return

    # If the user reacted with ✅, update the Elo rating
    if str(reaction.emoji) == '✅':
        
        
        if player_score > opponent_score:
            match = await Match.save_match(ctx.author, opponent, player_score, opponent_score)
        else:
            match = await Match.save_match(opponent, ctx.author, opponent_score, player_score)
        
        #make a result, showing how the elo of the players changed
        embed = discord.Embed(title="Match result", color=discord.Color.green())
        if player_score > opponent_score:
            winner = ctx.author
            looser = opponent
        else:
            winner = opponent
            looser = ctx.author
        
        embed.add_field(name="Winner", value=f"{winner.mention}\n{match.winner_elo_before} -> {match.winner_elo_after}\n+ {match.winner_elo_after - match.winner_elo_before} Elo", inline=True)
        embed.add_field(name="Looser", value=f"{looser.mention}\n{match.looser_elo_before} -> {match.looser_elo_after}\n -{match.looser_elo_before - match.looser_elo_after} Elo", inline=True)
        embed.add_field(name="Score", value=f"{match.score_winner}-{match.score_looser}", inline=True)

        await ctx.send(embed=embed)
        
    else:
        await ctx.send("Action cancelled. No Elo change.")
    

@bot.command()
async def matches(ctx, user: discord.Member = None, n: int = 5):
    
    if user is None:
        user = ctx.author
    
    n = min(n, 25)
    
    user = db.query(Member).filter(Member.discord_id == str(user.id)).first()
    # Get the last n matches
    matches = db.query(Match).filter(or_(Match.winner_id == user.id, Match.looser_id == user.id)).order_by(Match.date.desc()).limit(n).all()
    
    if not matches:
        await ctx.send(f"No matches found for {user.name}.")
        return

    # Create an embed to display the matches
    embed = discord.Embed(title=f"Last {n} matches for {user.name}", color=discord.Color.blue())
    for match in matches:
        winner = db.query(Member).filter(Member.id == match.winner_id).first()
        looser = db.query(Member).filter(Member.id == match.looser_id).first()
        embed.add_field(name=f"{winner.name} vs {looser.name}", value=f"Score: {match.score_winner}-{match.score_looser}\nDate: {match.date.strftime('%Y-%m-%d %H:%M:%S')}\n{winner.name}'s Elo change: {match.winner_elo_before} -> {match.winner_elo_after}\n{looser.name}'s Elo change: {match.looser_elo_before} -> {match.looser_elo_after}", inline=False)
    await ctx.send(embed=embed)