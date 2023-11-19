from requests import Session, Response
from data import InjuryStatus, Player, LineupChange, Game, PlayerStats, SlotType
from typing import List
from dateutil.parser import parse
from datetime import datetime

ESPN_READS_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/2024/segments/0/leagues"
ESPN_WRITES_URL = "https://lm-api-writes.fantasy.espn.com/apis/v3/games/fba/seasons/2024/segments/0/leagues"
ESPN_GAMES_URL = "https://site.api.espn.com/apis/fantasy/v2/games/fba/games"
LEAGUE_START_DATE = datetime(month=10, day=24, year=2023)

def get_scoring_period(date: datetime) -> int:
    delt = (date - LEAGUE_START_DATE).days
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

    def get_games(self, date: datetime) -> List[Game]:
        q = {"useMap": True, "dates": date.strftime("%Y/%m/%d"), "pbpOnly":True}
        events = check_response(self.sess.get(ESPN_GAMES_URL, params=q)).json()["events"]

        return [Game(evt["competitors"][0]["id"], evt["competitors"][1]["id"], parse(evt["date"])) for evt in events]


    def get_lineup(self, team_id: int, date: datetime) -> List[Player]:
        q = {"forTeamId": team_id, "scoringPeriodId": get_scoring_period(date), "view":"mRoster"}
        teams = check_response(self.sess.get(f"{ESPN_READS_URL}/{self.league_id}", params=q)).json()["teams"]
        roster = list(filter(lambda team: team["id"] == team_id, teams))[0]["roster"]["entries"]

        players = []

        for player in roster:
            stats_json_lst = sorted(
                player["playerPoolEntry"]["player"]["stats"], key=lambda j: j["seasonId"], reverse=True
            )

            sts = player["playerPoolEntry"]["player"]["injuryStatus"] 

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


    def update_lineup(self, team_id: int, date: datetime, changes: List[LineupChange]):
        if len(changes) > 0:
            id1 = get_scoring_period(date)
            id2 = get_scoring_period(datetime.now())

            b = {
                "teamId": team_id,
                "type": "ROSTER" if id1 == id2 else "FUTURE_ROSTER",
                "scoringPeriodId": id1,
                "executionType": "EXECUTE",
                "items":[{"playerId":change.player_id,"type":"LINEUP","toLineupSlotId":change.to_slot.value} for change in changes]
            }

            check_response(self.sess.post(f"{ESPN_WRITES_URL}/{self.league_id}/transactions", json=b))