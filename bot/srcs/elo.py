
import json
from srcs.utils import change_user_name
import os
from srcs.member import Member
from srcs.db import db

def get_elo(member):
    elos = get_elos()
    if str(member.id) in elos:
        return elos[str(member.id)]
    else:
        set_elo(member, 1000)
        return 1000

def get_elos():
    if not os.path.exists('database/elos.json'):
        return {}
    with open('database/elos.json', 'r') as file:
        elos = json.load(file)
    return elos


def calculate_elo(winner, looser, winner_k=32, looser_k=32):
    

    # Calculate the new Elo ratings
    expected_winner = 1 / (1 + 10 ** ((looser - winner) / 400))
    expected_looser = 1 / (1 + 10 ** ((winner - looser) / 400))

    return winner + winner_k * (1 - expected_winner), looser + looser_k * (0 - expected_looser)
    
    
async def change_elo(winner, looser, k=32):

    winner_db = db.query(Member).filter(Member.discord_id == str(winner.id)).first()
    looser_db = db.query(Member).filter(Member.discord_id == str(looser.id)).first()

    winner_count = len(winner_db.matches_won) + len(winner_db.matches_lost)
    looser_count = len(looser_db.matches_won) + len(looser_db.matches_lost)
    
    winner_k = k
    looser_k = k

    if winner_count < 10:
        winner_k += (10 - winner_count) * 12
        if looser_count >= 10:
            looser_k /= ((10 - looser_count) / 10) + 1
    
    if looser_count < 10:
        looser_k += (10 - looser_count) * 12
        if winner_count >= 10:
            winner_k /= ((10 - looser_count) / 10) + 1

    winner_db.elo, looser_db.elo = calculate_elo(winner_db.elo, looser_db.elo, winner_k, looser_k)
    
    # Save the changes to the database
    db.commit()
    await Member.refresh_name(winner)
    await Member.refresh_name(looser)
    return winner_db.elo, looser_db.elo

async def save_set(player1, player2, score1, score2):
        
    if score1 > score2:
        await change_elo(player1, player2)
    else:
        await change_elo(player2, player1)
        
    try:
        with open('database/elo_sets.json', 'r') as file:
            matches = json.load(file)
    except FileNotFoundError:
        matches = []

    matches.append({
        "player1": str(player1.id),
        "player2": str(player2.id),
        "score1": score1,
        "score2": score2
    })
    with open('database/elo_sets.json', 'w') as file:
        json.dump(matches, file)
  
    
def save_match(player1, player2, score1, score2):
    
    if abs(score1 - score2) == 1:
        weight = 42
    elif abs(score1 - score2) == 2:
        weight = 48
    elif abs(score1 - score2) == 3:
        weight = 56
    elif abs(score1 - score2) > 3:
        weight = 64
        
        
    
    if score1 > score2:
        change_elo(player1, player2, weight)
    else:
        change_elo(player2, player1, weight)
        
    try:
        with open('database/elo_matches.json', 'r') as file:
            matches = json.load(file)
    except FileNotFoundError:
        matches = []

    matches.append({
        "player1": str(player1.id),
        "player2": str(player2.id),
        "score1": score1,
        "score2": score2
    })
    with open('database/elo_matches.json', 'w') as file:
        json.dump(matches, file)

async def set_elo(member, elo):
    elos = get_elos()
    elos[str(member.id)] = elo
    with open('database/elos.json', 'w') as file:
        json.dump(elos, file)
    await reset_name(member)
    
async def reset_name(member):
    elo = get_elo(member)
    name = member.name.split(' (')[0]
    name = f"{name} ({elo})"
    await change_user_name(member, name)
