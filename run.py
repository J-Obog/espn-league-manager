import time
from client import ESPNFantasyClient
from manager import LeagueManager
from data import Date, InjuryStatus, LineupChange, SlotType
import dotenv
import os

dotenv.load_dotenv()

team_id = 1
curr_date = Date.just_date(11, 6, 2023)

league_manager = LeagueManager(
    ESPNFantasyClient(os.getenv("ESPN_S2"), os.getenv("LEAGUE_ID"))
)

league_manager.set_lineup(team_id, curr_date)