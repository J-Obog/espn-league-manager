from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum, IntEnum
from typing import Optional, List, Set
from datetime import datetime, date

class InjuryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    OUT = "OUT"
    SUSPENSION = "SUSPENSION"
    DAY_TO_DAY = "DAY_TO_DAY"

    @staticmethod
    def can_play(status: InjuryStatus) -> bool:
        return (status == InjuryStatus.ACTIVE) or (status == InjuryStatus.DAY_TO_DAY) 

@dataclass
class Date:
    month: int
    day: int
    year: int
    hour: int
    minute: int

    @staticmethod
    def curr_date() -> Date:
        t_now = datetime.now()
        return Date(month=t_now.month, day=t_now.day, year=t_now.year, hour=t_now.hour, minute=t_now.minute)

    @staticmethod
    def just_date(month: int, day: int, year: int) -> Date:
        return Date(month=month, day=day, year=year, hour=0, minute=0)  

    @staticmethod
    def days_delta(start: Date, end: Date) -> int:
        d0 = date(start.year, start.month, start.day) 
        d1 = date(end.year, end.month, end.day)
        delta = d1 - d0
        return delta.days

@dataclass
class PlayerRating:
    total_ranking: int

@dataclass
class PlayerStats:
    projected_average_fp: float 

class SlotType(IntEnum):
    PG = 0
    SG = 1
    SF = 2
    PF = 3
    C = 4
    G = 5
    F = 6
    UTIL = 11
    BENCH = 12

    @staticmethod
    def get_or_none(slot: int) -> Optional[SlotType]:
        try:
            return SlotType(slot)
        except:
            return None


@dataclass
class Player:
    id: int
    team_id: int
    name: str
    slot: SlotType
    eligible_slots: Set[int]
    injury_status: InjuryStatus
    stats: PlayerStats

@dataclass
class LineupChange:
    player_id: int
    to_slot: SlotType

@dataclass
class Game:
    team_a_id: int
    team_b_id: int
    date: Date
