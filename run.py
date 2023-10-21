import time
from client import ESPNFantasyClient
from data import Date, InjuryStatus, LineupChange, SlotType
import dotenv
import os

dotenv.load_dotenv()

team_id = 1
curr_date = Date.just_date(10, 28, 2023)

espn_client = ESPNFantasyClient(os.getenv("ESPN_S2"), os.getenv("LEAGUE_ID"))

games = espn_client.get_games(curr_date)
teams_playing = set()

for game in games:
    teams_playing.add(int(game.team_a_id))
    teams_playing.add(int(game.team_b_id))

lineup = espn_client.get_lineup(team_id, curr_date)

bench_changes = [LineupChange(player.id, SlotType.BENCH) for player in lineup if player.slot != SlotType.BENCH]
if len(bench_changes) > 0:
    espn_client.update_lineup(team_id, curr_date, bench_changes)
    time.sleep(1)

playing_players = list(filter(lambda p: (p.team_id in teams_playing) and (InjuryStatus.can_play(p.injury_status)), lineup))
playing_players = sorted(playing_players, key=lambda p: p.stats.projected_average_fp, reverse=True)

changes = []

slot_rotation = [
    SlotType.PG, 
    SlotType.SG, 
    SlotType.SF,
    SlotType.PF,
    SlotType.C,
    SlotType.G,
    SlotType.F,
    SlotType.UTIL,
    SlotType.UTIL, 
    SlotType.UTIL
] 

for pos in slot_rotation:
    for player in playing_players:
        if (player.slot == SlotType.BENCH) and (pos in player.eligible_slots):
            player.slot = pos
            print(player.slot, player.name)
            changes.append(LineupChange(player.id, pos))
            break

espn_client.update_lineup(team_id, curr_date, changes)