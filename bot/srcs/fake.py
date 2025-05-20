

from faker import Faker
from srcs.db import db
from srcs.member import Member
from srcs.match import Match
from srcs.elo import calculate_elo
import random
def fake_db():


    fake = Faker()
    users = []
    for _ in range(100):
        name = fake.name()
        discord_id = fake.uuid4()
        elo = fake.random_int(min=100, max=3000)
        new_user = Member(name=name, discord_id=str(discord_id), elo=elo)
        db.add(new_user)
        users += [new_user]
        
        db.commit()
    
    for _ in range(100):
        player1 = random.choice(users)
        player2 = random.choice(users)
        while player1 == player2:
            player2 = random.choice(users)
        
        expected_winner = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
        if random.random() < expected_winner:
            winner = player1
            looser = player2
        else:
            winner = player2
            looser = player1

        winner.elo, looser.elo = calculate_elo(winner.elo, looser.elo)
        
        match = Match(winner_id=winner.id, looser_id=looser.id, score_winner=1, score_looser=0)
        db.add(match)
        
        db.commit()