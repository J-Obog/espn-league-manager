import time
from client import ESPNFantasyClient
from data import Date, InjuryStatus, LineupChange
import dotenv
import os

dotenv.load_dotenv()

team_id = 1
curr_date = Date.just_date(10, 24, 2023) 

league_id = 62409110
espn_client = ESPNFantasyClient(os.getenv("ESPN_S2"), 62409110)

print(espn_client.get_games(curr_date))
#print(espn_client.get_lineup(team_id, curr_date))