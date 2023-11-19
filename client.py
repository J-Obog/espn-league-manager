import time
from requests import Session, Response
from data import InjuryStatus, Player, Date, LineupChange, Game, PlayerRating, PlayerStats, SlotType
from typing import List
from dateutil.parser import parse

ESPN_READS_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/2024/segments/0/leagues"
ESPN_WRITES_URL = "https://lm-api-writes.fantasy.espn.com/apis/v3/games/fba/seasons/2024/segments/0/leagues"
ESPN_GAMES_URL = "https://site.api.espn.com/apis/fantasy/v2/games/fba/games"
LEAGUE_START_DATE = Date.just_date(10, 24, 2023) 

def scoring_period_id_by_date(date: Date) -> int:
    delt = Date.days_delta(LEAGUE_START_DATE, date)
    return 1 if delt < 0 else delt + 1

def check_response(res: Response) -> Response:
        if res.status_code != 200: 
            raise Exception(res.content)
        return res

# TODO: search by seasonId?
def get_projected_fp(stat_json: List[dict[str, any]]) -> float:
    for s in stat_json:
        if s["statSourceId"] == 1 and s["statSplitTypeId"] == 0:
         return s["appliedAverage"]
    return 0.0 # TODO: use current season stats if projected is not available 

class ESPNFantasyClient:
    def __init__(self, espn_s2_cookie: str, league_id: int):
        self.sess = Session()
        self.league_id = league_id
        self.sess.cookies["espn_s2"] = espn_s2_cookie
        self.sess.headers["Cache-Control"] = "no-cache"

    def get_games(self, date: Date) -> List[Game]:
        mm = str(date.month) if date.month >= 10 else f"0{date.month}"
        dd = str(date.day) if date.day >= 10 else f"0{date.day}"

        url = f"{ESPN_GAMES_URL}"
        q = {"useMap": True, "dates": f"{date.year}{mm}{dd}", "pbpOnly":True}
        res = check_response(self.sess.get(url, params=q)).json()
        events_json = res["events"]

        games = []

        for event_json in events_json:
            dt = parse(event_json["date"])

            games.append(Game(
                  team_a_id=event_json["competitors"][0]["id"],
                  team_b_id=event_json["competitors"][1]["id"],
                  date=Date(month=dt.month, day=dt.day, year=dt.year, hour=dt.hour, minute=dt.minute)
             ))

        return games

    def get_lineup(self, team_id: int, date: Date) -> List[Player]:
        url = f"{ESPN_READS_URL}/{self.league_id}"
        spid = scoring_period_id_by_date(date)

        q = {"forTeamId": team_id, "scoringPeriodId": spid, "view":"mRoster"}
        res = check_response(self.sess.get(url, params=q)).json()
        roster_json = list(filter(lambda tj: tj["id"] == team_id, res["teams"]))[0]["roster"]["entries"]
        players = []

        for player in roster_json:
            stats_json_lst = sorted(
                player["playerPoolEntry"]["player"]["stats"], key=lambda j: j["seasonId"], reverse=True
            )

            sts = player["playerPoolEntry"]["player"]["injuryStatus"] 
            print(player["playerPoolEntry"]["player"]["fullName"])

            players.append(
                Player(
                    id=player["playerPoolEntry"]["player"]["id"],
                    team_id=player["playerPoolEntry"]["player"]["proTeamId"],
                    name=player["playerPoolEntry"]["player"]["fullName"],
                    slot=SlotType(player["lineupSlotId"]),
                    eligible_slots=set([SlotType.get_or_none(slot) for slot in player["playerPoolEntry"]["player"]["eligibleSlots"]]),
                    injury_status=InjuryStatus(sts),
                    stats=PlayerStats(
                        projected_average_fp=get_projected_fp(stats_json_lst)
                    )
                )
            )

        return players


    def update_lineup(self, team_id: int, date: Date, changes: List[LineupChange]):
        if len(changes) > 0:
            url = f"{ESPN_WRITES_URL}/{self.league_id}/transactions"

            id1 = scoring_period_id_by_date(date)
            id2 = scoring_period_id_by_date(Date.curr_date())

            roster_type = "ROSTER" if id1 == id2 else "FUTURE_ROSTER"

            b = {"teamId":team_id,"type":roster_type,"scoringPeriodId":id1,"executionType":"EXECUTE","items":[]}
            
            for change in changes:
                b["items"].append({"playerId":change.player_id,"type":"LINEUP","toLineupSlotId":change.to_slot.value})
                
            check_response(self.sess.post(url, json=b))