from dataclasses import dataclass
from typing import Optional, List
from datetime import date


@dataclass
class Calendar:
    start: date
    end: date
    today: date
    closed: List[date]
    scale: str


@dataclass
class Task:
    name: str
    text: str
    plan_start: date
    plan_end: date
    color_plan_fill: str
    color_plan_outline: str
    color_actual_fill: str
    color_actual_outline: str
    color_text: str
    actual_start: Optional[date] = None
    actual_completed: Optional[date] = None
    actual_progress: Optional[str] = None
    actual_end: Optional[date] = None
    assignee: Optional[str] = None


@dataclass
class Milestone:
    name: str
    text: str
    plan_happen: date
    color_plan_fill: str
    color_plan_outline: str
    color_actual_fill: str
    color_actual_outline: str
    color_text: str
    actual_happen: Optional[date] = None


@dataclass(frozen=True)
class DependencyPath:
    start_name: str
    start_date: date
    end_name: str
    end_date: date
    color: str


@dataclass
class Group:
    text: str
    member: List[str]
