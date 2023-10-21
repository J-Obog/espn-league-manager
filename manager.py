from client import ESPNFantasyClient
from data import Date, LineupChange, SlotType, InjuryStatus
import time

SLOT_ROTATION = [
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

class LeagueManager:
    def __init__(self, client: ESPNFantasyClient):
        self.client = client
    

    def set_lineup(self, team_id: int, date: Date):
        games = self.client.get_games(date)
        teams_playing = set()
        
        for game in games:
            teams_playing.add(int(game.team_a_id))
            teams_playing.add(int(game.team_b_id))
            
        lineup = self.client.get_lineup(team_id, date)

        bench_changes = []
        for p in lineup:
            if p.slot != SlotType.BENCH:
                p.slot = SlotType.BENCH
                bench_changes.append(LineupChange(p.id, SlotType.BENCH))

        if len(bench_changes) > 0:
            self.client.update_lineup(team_id, date, bench_changes)
            time.sleep(2)
            
        playing_players = list(filter(lambda p: (p.team_id in teams_playing) and (InjuryStatus.can_play(p.injury_status)), lineup))
        playing_players = sorted(playing_players, key=lambda p: p.stats.projected_average_fp, reverse=True)
        
        changes = []
        
        for pos in SLOT_ROTATION:
            for player in playing_players:
                if (player.slot == SlotType.BENCH) and (pos in player.eligible_slots):
                    player.slot = pos           
                    changes.append(LineupChange(player.id, pos))
                    break

        self.client.update_lineup(team_id, date, changes)
