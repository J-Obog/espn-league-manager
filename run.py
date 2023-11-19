import time
from client import ESPNFantasyClient
from manager import LeagueManager
from data import Date
import dotenv
import os
import logging
import time
import redis

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(level = logging.INFO)

dotenv.load_dotenv()

#r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0)


team_id = 1

start_date = Date.just_date(11, 18, 2023)
end_date = Date.just_date(11, 30, 2023)

league_manager = LeagueManager(
    ESPNFantasyClient(os.getenv("ESPN_S2"), os.getenv("LEAGUE_ID"))
)

curr_date = start_date
while (Date.days_delta(curr_date, end_date) >= 0):
    league_manager.set_lineup(team_id, curr_date)
    curr_date.add_days(1)    
    time.sleep(0.125)

