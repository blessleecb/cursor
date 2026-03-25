from __future__ import annotations

import html
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "workout_app.db"
STATIC_DIR = BASE_DIR / "static"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


EXERCISES: list[dict[str, Any]] = [
    {"slug": "barbell-bench-press", "name": "바벨 벤치프레스", "description": "평평한 벤치에서 바벨을 가슴까지 내렸다가 밀어 올리며 가슴과 삼두를 강화하는 대표적인 프레스 운동입니다.", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "incline-dumbbell-press", "name": "인클라인 덤벨 프레스", "description": "상체를 기울인 벤치에서 덤벨을 밀어 올려 윗가슴과 전면 어깨를 자극하는 운동입니다.", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 0},
    {"slug": "machine-chest-press", "name": "머신 체스트 프레스", "description": "머신 궤도를 따라 밀어내며 가슴을 안정적으로 자극할 수 있는 프레스 운동입니다.", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "cable-fly", "name": "케이블 플라이", "description": "양손 케이블을 모으는 동작으로 가슴 수축 구간을 길게 가져가는 고립 운동입니다.", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "push-up", "name": "푸시업", "description": "체중을 이용해 가슴, 삼두, 코어를 함께 사용하는 기본적인 밀기 운동입니다.", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "weighted-dip", "name": "중량 딥스", "description": "평행봉에서 몸을 내렸다가 밀어 올리며 가슴 하부와 삼두를 강하게 자극하는 운동입니다.", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "pull-up", "name": "풀업", "description": "철봉을 잡고 몸을 끌어올려 광배와 상완이두를 강화하는 대표적인 당기기 운동입니다.", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "weighted-pull-up", "name": "중량 풀업", "description": "추가 중량을 달고 수행하는 풀업으로 등 전반의 힘과 상완 이두를 함께 강화합니다.", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "barbell-row", "name": "바벨 로우", "description": "상체를 숙인 상태에서 바벨을 몸쪽으로 당겨 광배와 후면 어깨, 등 두께를 키우는 운동입니다.", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "chest-supported-row", "name": "체스트 서포티드 로우", "description": "가슴을 지지한 상태로 당겨 허리 부담을 줄이며 등 수축에 집중하는 로우 운동입니다.", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "lat-pulldown", "name": "랫풀다운", "description": "상단 케이블 바를 가슴 방향으로 당겨 광배를 집중적으로 자극하는 머신 운동입니다.", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "single-arm-cable-row", "name": "원암 케이블 로우", "description": "한 팔씩 케이블을 당기며 좌우 밸런스와 광배 수축을 세밀하게 조절할 수 있는 운동입니다.", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "deadlift", "name": "데드리프트", "description": "바닥의 바벨을 들어 올리며 하체 후면과 등, 코어를 함께 사용하는 전신 복합 운동입니다.", "muscle_group": "legs", "secondary_group": "back", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "back-squat", "name": "백 스쿼트", "description": "바벨을 등에 올리고 앉았다 일어서며 하체 전반의 힘과 근육량을 키우는 대표 운동입니다.", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "front-squat", "name": "프론트 스쿼트", "description": "바벨을 앞쪽에 걸치고 수행해 대퇴사두와 코어 개입이 큰 스쿼트 변형입니다.", "muscle_group": "legs", "secondary_group": "core", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "leg-press", "name": "레그 프레스", "description": "발판을 밀어내며 허리 부담을 줄인 상태에서 대퇴사두와 둔근을 자극하는 머신 운동입니다.", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "romanian-deadlift", "name": "루마니안 데드리프트", "description": "힙힌지를 유지하며 바벨을 내렸다 올려 햄스트링과 둔근을 늘려 자극하는 운동입니다.", "muscle_group": "hamstrings", "secondary_group": "glutes", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "lying-leg-curl", "name": "라잉 레그컬", "description": "엎드린 자세에서 무릎을 굽혀 햄스트링을 직접적으로 자극하는 머신 운동입니다.", "muscle_group": "hamstrings", "secondary_group": "calves", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "bulgarian-split-squat", "name": "불가리안 스플릿 스쿼트", "description": "한쪽 발을 뒤에 두고 수행해 둔근과 대퇴사두, 균형 능력을 함께 키우는 운동입니다.", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "walking-lunge", "name": "워킹 런지", "description": "걸으며 런지를 반복해 하체 전면과 둔근, 균형 능력을 동시에 자극하는 운동입니다.", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "barbell-overhead-press", "name": "바벨 오버헤드 프레스", "description": "바벨을 머리 위로 밀어 올려 어깨와 삼두의 힘을 기르는 수직 프레스 운동입니다.", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "seated-dumbbell-press", "name": "시티드 덤벨 프레스", "description": "앉은 자세에서 덤벨을 밀어 올려 어깨 전면과 측면을 안정적으로 자극하는 운동입니다.", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 0},
    {"slug": "machine-shoulder-press", "name": "머신 숄더 프레스", "description": "머신을 이용해 어깨와 삼두에 지속적인 긴장을 주는 프레스 운동입니다.", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "lateral-raise", "name": "사이드 레터럴 레이즈", "description": "덤벨을 옆으로 들어 올려 측면 삼각근을 집중적으로 키우는 고립 운동입니다.", "muscle_group": "side delts", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "cable-lateral-raise", "name": "케이블 레터럴 레이즈", "description": "케이블 저항으로 전 구간 긴장을 유지하며 측면 삼각근을 자극하는 운동입니다.", "muscle_group": "side delts", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "rear-delt-fly", "name": "리어 델트 플라이", "description": "후면 삼각근을 겨냥해 팔을 벌려 어깨 뒤쪽과 상부 등을 자극하는 운동입니다.", "muscle_group": "rear delts", "secondary_group": "upper back", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "face-pull", "name": "페이스 풀", "description": "얼굴 방향으로 케이블을 당겨 후면 어깨와 견갑 주변 안정성을 높이는 운동입니다.", "muscle_group": "rear delts", "secondary_group": "upper back", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "upright-row", "name": "업라이트 로우", "description": "바를 몸 가까이 세워 당겨 측면 어깨와 승모를 함께 자극하는 운동입니다.", "muscle_group": "side delts", "secondary_group": "traps", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "barbell-curl", "name": "바벨 컬", "description": "바벨을 들어 올려 상완이두를 중량감 있게 자극하는 기본 팔 운동입니다.", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "incline-dumbbell-curl", "name": "인클라인 덤벨 컬", "description": "기울어진 벤치에 기대어 수행해 이두근이 늘어난 구간을 길게 쓰는 컬 운동입니다.", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "hammer-curl", "name": "해머 컬", "description": "중립 그립으로 들어 올려 이두와 전완, 상완근을 함께 자극하는 운동입니다.", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "cable-curl", "name": "케이블 컬", "description": "케이블 저항으로 수축 구간 긴장을 유지하며 이두를 자극하는 운동입니다.", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "ez-bar-curl", "name": "EZ바 컬", "description": "손목 부담을 줄인 EZ바로 이두근을 고중량까지 다루기 좋은 컬 운동입니다.", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "close-grip-bench-press", "name": "클로즈그립 벤치프레스", "description": "좁은 그립으로 벤치프레스를 수행해 삼두 중심으로 힘을 키우는 프레스 운동입니다.", "muscle_group": "triceps", "secondary_group": "chest", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "cable-pushdown", "name": "케이블 푸시다운", "description": "상완을 고정한 채 케이블을 아래로 밀어 삼두를 수축시키는 대표 고립 운동입니다.", "muscle_group": "triceps", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "overhead-triceps-extension", "name": "오버헤드 트라이셉스 익스텐션", "description": "머리 위에서 케이블이나 손잡이를 펴며 삼두 장두를 길게 자극하는 운동입니다.", "muscle_group": "triceps", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "skull-crusher", "name": "스컬 크러셔", "description": "누운 상태에서 팔꿈치를 굽혔다 펴며 삼두를 직접 자극하는 프리웨이트 운동입니다.", "muscle_group": "triceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "single-arm-pushdown", "name": "원암 푸시다운", "description": "한 팔씩 케이블을 밀어 삼두 좌우 밸런스를 맞추기 좋은 보조 운동입니다.", "muscle_group": "triceps", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "standing-calf-raise", "name": "스탠딩 카프 레이즈", "description": "서서 발목을 펴며 비복근을 중심으로 종아리를 자극하는 운동입니다.", "muscle_group": "calves", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "seated-calf-raise", "name": "시티드 카프 레이즈", "description": "앉은 자세에서 발목을 들어 올려 가자미근 중심으로 종아리를 강화하는 운동입니다.", "muscle_group": "calves", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "hip-thrust", "name": "힙 쓰러스트", "description": "엉덩이를 위로 밀어 올리며 둔근을 강하게 수축시키는 대표적인 둔근 운동입니다.", "muscle_group": "glutes", "secondary_group": "hamstrings", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "glute-bridge", "name": "글루트 브리지", "description": "바닥에서 골반을 들어 올려 둔근과 햄스트링을 부담 적게 자극하는 운동입니다.", "muscle_group": "glutes", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "leg-extension", "name": "레그 익스텐션", "description": "무릎을 펴며 대퇴사두를 직접 자극하는 대표적인 머신 고립 운동입니다.", "muscle_group": "legs", "secondary_group": "quads", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "hack-squat", "name": "핵 스쿼트", "description": "고정된 궤도에서 하체를 밀어 올려 대퇴사두와 둔근을 고중량으로 다루기 좋은 운동입니다.", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "strength", "equipment": "machine", "is_unilateral": 0},
    {"slug": "good-morning", "name": "굿모닝", "description": "상체를 접었다 펴는 힙힌지 동작으로 햄스트링과 척추기립근을 강화하는 운동입니다.", "muscle_group": "hamstrings", "secondary_group": "back", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "t-bar-row", "name": "티바 로우", "description": "티바 손잡이를 몸쪽으로 당겨 광배와 등 두께를 집중적으로 키우는 로우 운동입니다.", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "machine-row", "name": "머신 로우", "description": "머신을 활용해 안정적으로 광배와 능형근을 수축시키는 등 운동입니다.", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "pec-deck", "name": "펙덱 플라이", "description": "팔을 모으는 머신 궤도로 가슴 안쪽 수축을 집중 공략하는 운동입니다.", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
]


SPLIT_DEFINITIONS = {
    "2-day": {
        "label": "2분할",
        "description": "등가슴 / 하체어깨",
        "days": [
            {"name": "Day 1", "focus": "등가슴", "groups": ["back", "chest"]},
            {"name": "Day 2", "focus": "하체어깨", "groups": ["legs", "shoulders"]},
        ],
    },
    "3-day": {
        "label": "3분할",
        "description": "가슴 / 등 / 하체어깨",
        "days": [
            {"name": "Day 1", "focus": "가슴", "groups": ["chest"]},
            {"name": "Day 2", "focus": "등", "groups": ["back"]},
            {"name": "Day 3", "focus": "하체어깨", "groups": ["legs", "shoulders"]},
        ],
    },
}


PRIMARY_ROUTINE_CHOICES = {
    "chest": {"strength": "barbell-bench-press", "hypertrophy": "incline-dumbbell-press"},
    "back": {"strength": "weighted-pull-up", "hypertrophy": "chest-supported-row"},
    "legs": {"strength": "back-squat", "hypertrophy": "leg-press"},
    "shoulders": {"strength": "barbell-overhead-press", "hypertrophy": "seated-dumbbell-press"},
}


ACCESSORY_CHOICES = [
    ("rear delts", "face-pull"),
    ("biceps", "incline-dumbbell-curl"),
    ("triceps", "cable-pushdown"),
]


MUSCLE_COLORS = {
    "chest": ("#f97316", "#fed7aa"),
    "back": ("#2563eb", "#bfdbfe"),
    "legs": ("#16a34a", "#bbf7d0"),
    "shoulders": ("#7c3aed", "#ddd6fe"),
    "rear delts": ("#db2777", "#fbcfe8"),
    "side delts": ("#8b5cf6", "#ddd6fe"),
    "biceps": ("#0f766e", "#99f6e4"),
    "triceps": ("#dc2626", "#fecaca"),
    "hamstrings": ("#15803d", "#bbf7d0"),
    "glutes": ("#c2410c", "#fdba74"),
    "calves": ("#475569", "#cbd5e1"),
}

MUSCLE_LABELS = {
    "chest": "가슴",
    "back": "등",
    "legs": "하체",
    "shoulders": "어깨",
    "rear delts": "후면 어깨",
    "side delts": "측면 어깨",
    "biceps": "이두",
    "triceps": "삼두",
    "hamstrings": "햄스트링",
    "glutes": "둔근",
    "calves": "종아리",
    "front delts": "전면 어깨",
    "upper back": "상부 등",
    "traps": "승모",
    "forearms": "전완",
    "core": "코어",
    "quads": "대퇴사두",
}

EQUIPMENT_LABELS = {
    "barbell": "바벨",
    "dumbbell": "덤벨",
    "machine": "머신",
    "cable": "케이블",
    "bodyweight": "맨몸",
}

MOVEMENT_LABELS = {
    "strength": "스트렝스",
    "hypertrophy": "근비대",
}


class RoutineGenerateRequest(BaseModel):
    split_type: str = Field(pattern="^(2-day|3-day)$")


class RoutineExercisePayload(BaseModel):
    id: Optional[int] = None
    day_name: str
    day_order: int
    focus: str
    exercise_id: int
    role: str
    set_count: int
    rep_range: str
    notes: str = ""
    target_weight: Optional[float] = None


class RoutineUpdateRequest(BaseModel):
    split_type: str = Field(pattern="^(2-day|3-day)$")
    days: list[RoutineExercisePayload]


class WorkoutSetPayload(BaseModel):
    exercise_id: int
    set_type: str
    set_number: int
    weight: float
    reps: int
    notes: str = ""


class WorkoutLogRequest(BaseModel):
    performed_on: str
    split_type: str
    day_name: str
    entries: list[WorkoutSetPayload]


@dataclass
class SetTargets:
    set_count: int
    rep_range: str


def create_tables() -> None:
    with closing(get_connection()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                muscle_group TEXT NOT NULL,
                secondary_group TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                equipment TEXT NOT NULL,
                is_unilateral INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS routines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                split_type TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS routine_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_id INTEGER NOT NULL,
                day_name TEXT NOT NULL,
                day_order INTEGER NOT NULL,
                focus TEXT NOT NULL,
                exercise_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                set_count INTEGER NOT NULL,
                rep_range TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                target_weight REAL,
                FOREIGN KEY (routine_id) REFERENCES routines(id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id)
            );

            CREATE TABLE IF NOT EXISTS workout_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                performed_on TEXT NOT NULL,
                split_type TEXT NOT NULL,
                day_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workout_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                set_type TEXT NOT NULL,
                set_number INTEGER NOT NULL,
                weight REAL NOT NULL,
                reps INTEGER NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (session_id) REFERENCES workout_sessions(id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id)
            );
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(exercises)").fetchall()}
        if "description" not in columns:
            conn.execute("ALTER TABLE exercises ADD COLUMN description TEXT NOT NULL DEFAULT ''")
        conn.commit()


def seed_exercises() -> None:
    with closing(get_connection()) as conn:
        conn.executemany(
            """
            INSERT INTO exercises
            (slug, name, description, muscle_group, secondary_group, movement_type, equipment, is_unilateral)
            VALUES (:slug, :name, :description, :muscle_group, :secondary_group, :movement_type, :equipment, :is_unilateral)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                muscle_group = excluded.muscle_group,
                secondary_group = excluded.secondary_group,
                movement_type = excluded.movement_type,
                equipment = excluded.equipment,
                is_unilateral = excluded.is_unilateral
            """,
            EXERCISES,
        )
        conn.commit()


def enrich_exercise_payload(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["muscle_group_label"] = MUSCLE_LABELS.get(item["muscle_group"], item["muscle_group"])
    item["secondary_group_label"] = MUSCLE_LABELS.get(item["secondary_group"], item["secondary_group"])
    item["movement_type_label"] = MOVEMENT_LABELS.get(item["movement_type"], item["movement_type"])
    item["equipment_label"] = EQUIPMENT_LABELS.get(item["equipment"], item["equipment"])
    item["laterality_label"] = "단측" if item["is_unilateral"] else "양측"
    return item


def fetch_exercise_map(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    rows = conn.execute("SELECT * FROM exercises").fetchall()
    return {row["slug"]: row for row in rows}


def default_targets(role: str) -> SetTargets:
    if role == "strength":
        return SetTargets(4, "웜업 8회 / 탑세트 4-6회 / 탑세트 4-6회 / 백오프 6-8회")
    if role == "hypertrophy":
        return SetTargets(3, "8-12회")
    return SetTargets(3, "12-20회")


def suggest_initial_weight(exercise_name: str, role: str) -> float:
    base = 20.0
    name = exercise_name.lower()
    if "스쿼트" in exercise_name or "데드리프트" in exercise_name or "레그 프레스" in exercise_name:
        base = 60.0
    elif "로우" in exercise_name or "프레스" in exercise_name or "풀업" in exercise_name:
        base = 40.0
    elif "컬" in exercise_name or "레이즈" in exercise_name or "푸시다운" in exercise_name:
        base = 12.5
    return base if role != "accessory" else max(7.5, base / 2)


def build_default_routine(split_type: str, conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if split_type not in SPLIT_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Unsupported split type")
    exercise_map = fetch_exercise_map(conn)
    routine_days: list[dict[str, Any]] = []
    for index, day in enumerate(SPLIT_DEFINITIONS[split_type]["days"], start=1):
        for group in day["groups"]:
            if group in PRIMARY_ROUTINE_CHOICES:
                for role in ("strength", "hypertrophy"):
                    target = default_targets(role)
                    exercise = exercise_map[PRIMARY_ROUTINE_CHOICES[group][role]]
                    routine_days.append(
                        {
                            "day_name": day["name"],
                            "day_order": index,
                            "focus": day["focus"],
                            "exercise_id": exercise["id"],
                            "role": role,
                            "set_count": target.set_count,
                            "rep_range": target.rep_range,
                            "notes": f"{MUSCLE_LABELS.get(group, group)} {MOVEMENT_LABELS.get(role, role)} 우선 종목",
                            "target_weight": suggest_initial_weight(exercise["name"], role),
                        }
                    )
        for accessory_group, slug in ACCESSORY_CHOICES:
            exercise = exercise_map[slug]
            target = default_targets("accessory")
            routine_days.append(
                {
                    "day_name": day["name"],
                    "day_order": index,
                    "focus": day["focus"],
                    "exercise_id": exercise["id"],
                    "role": "accessory",
                    "set_count": target.set_count,
                    "rep_range": target.rep_range,
                    "notes": f"{MUSCLE_LABELS.get(accessory_group, accessory_group)} 보조 종목",
                    "target_weight": suggest_initial_weight(exercise["name"], "accessory"),
                }
            )
    return routine_days


def create_or_replace_routine(split_type: str, days: list[dict[str, Any]]) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with closing(get_connection()) as conn:
        conn.execute("UPDATE routines SET is_active = 0 WHERE is_active = 1")
        cursor = conn.execute(
            "INSERT INTO routines (split_type, is_active, created_at) VALUES (?, 1, ?)",
            (split_type, now),
        )
        routine_id = cursor.lastrowid
        conn.executemany(
            """
            INSERT INTO routine_days
            (routine_id, day_name, day_order, focus, exercise_id, role, set_count, rep_range, notes, target_weight)
            VALUES (:routine_id, :day_name, :day_order, :focus, :exercise_id, :role, :set_count, :rep_range, :notes, :target_weight)
            """,
            [{**day, "routine_id": routine_id} for day in days],
        )
        conn.commit()
        return routine_id


def get_active_routine(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM routines WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()


def fetch_routine_payload() -> Optional[dict[str, Any]]:
    with closing(get_connection()) as conn:
        routine = get_active_routine(conn)
        if not routine:
            return None
        rows = conn.execute(
            """
            SELECT rd.*, e.name, e.slug, e.description, e.muscle_group, e.secondary_group, e.equipment, e.movement_type, e.is_unilateral
            FROM routine_days rd
            JOIN exercises e ON e.id = rd.exercise_id
            WHERE rd.routine_id = ?
            ORDER BY rd.day_order, rd.role, rd.id
            """,
            (routine["id"],),
        ).fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["day_name"], []).append(enrich_exercise_payload(row))
        return {"routine": dict(routine), "days": grouped}


def compute_estimated_1rm(weight: float, reps: int) -> float:
    return round(weight * (1 + reps / 30), 1)


def load_latest_exercise_performance(conn: sqlite3.Connection, exercise_id: int) -> list[sqlite3.Row]:
    session = conn.execute(
        """
        SELECT ws.session_id
        FROM workout_sets ws
        JOIN workout_sessions s ON s.id = ws.session_id
        WHERE ws.exercise_id = ?
        ORDER BY s.performed_on DESC, ws.id DESC
        LIMIT 1
        """,
        (exercise_id,),
    ).fetchone()
    if not session:
        return []
    return conn.execute(
        """
        SELECT ws.*, e.name, e.muscle_group
        FROM workout_sets ws
        JOIN exercises e ON e.id = ws.exercise_id
        WHERE ws.exercise_id = ? AND ws.session_id = ?
        ORDER BY ws.set_number
        """,
        (exercise_id, session["session_id"]),
    ).fetchall()


def recommend_next_weight(
    exercise: sqlite3.Row, routine_entry: Optional[sqlite3.Row], latest_sets: list[sqlite3.Row]
) -> dict[str, Any]:
    baseline = routine_entry["target_weight"] if routine_entry and routine_entry["target_weight"] else suggest_initial_weight(exercise["name"], exercise["movement_type"])
    increment = 5.0 if exercise["muscle_group"] in {"legs", "hamstrings", "glutes"} else 2.5
    if not latest_sets:
        return {"recommended_weight": baseline, "reason": "기록이 없어 기본 권장 중량을 사용합니다."}
    avg_reps = sum(item["reps"] for item in latest_sets) / len(latest_sets)
    avg_weight = sum(item["weight"] for item in latest_sets) / len(latest_sets)
    if avg_reps >= 11:
        return {"recommended_weight": round(avg_weight + increment, 1), "reason": "직전 수행에서 반복 수가 상단 범위를 충족해 증량을 권장합니다."}
    if avg_reps >= 8:
        return {"recommended_weight": round(avg_weight, 1), "reason": "직전 수행이 목표 범위에 들어 유지 권장입니다."}
    return {"recommended_weight": round(max(avg_weight - increment / 2, increment), 1), "reason": "직전 반복 수가 낮아 미세 감량 또는 유지가 적절합니다."}


def init_db() -> None:
    create_tables()
    seed_exercises()


def exercise_artwork_path(exercise: dict[str, Any]) -> str:
    if exercise["muscle_group"] in {"legs", "hamstrings", "glutes", "calves"}:
        return "/static/assets/exercise-icons/walking.svg"
    if exercise["equipment"] == "barbell":
        return "/static/assets/exercise-icons/barbell.svg"
    if exercise["equipment"] == "dumbbell":
        return "/static/assets/exercise-icons/dumbbell.svg"
    if exercise["equipment"] == "bodyweight":
        return "/static/assets/exercise-icons/body.svg"
    if exercise["movement_type"] == "strength":
        return "/static/assets/exercise-icons/exercise-weights.svg"
    return "/static/assets/exercise-icons/gym.svg"


def get_exercises_payload(group: Optional[str] = None) -> list[dict[str, Any]]:
    with closing(get_connection()) as conn:
        if group:
            rows = conn.execute(
                "SELECT * FROM exercises WHERE muscle_group = ? ORDER BY name",
                (group,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM exercises ORDER BY muscle_group, name").fetchall()
        return [enrich_exercise_payload(row) for row in rows]


def get_progress_payload(limit: int = 12) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        volume_rows = conn.execute(
            """
            SELECT e.muscle_group, s.performed_on, ROUND(SUM(ws.weight * ws.reps), 1) AS volume
            FROM workout_sets ws
            JOIN exercises e ON e.id = ws.exercise_id
            JOIN workout_sessions s ON s.id = ws.session_id
            GROUP BY e.muscle_group, s.performed_on
            ORDER BY s.performed_on DESC
            LIMIT ?
            """,
            (limit * 6,),
        ).fetchall()
        best_rows = conn.execute(
            """
            SELECT e.name, e.muscle_group, MAX(ws.weight) AS max_weight, MAX((ws.weight * (1 + (ws.reps / 30.0)))) AS estimated_1rm
            FROM workout_sets ws
            JOIN exercises e ON e.id = ws.exercise_id
            GROUP BY e.id
            ORDER BY estimated_1rm DESC
            LIMIT 12
            """
        ).fetchall()
        recent_sessions = conn.execute(
            """
            SELECT s.performed_on, s.day_name, COUNT(ws.id) AS sets_logged
            FROM workout_sessions s
            LEFT JOIN workout_sets ws ON ws.session_id = s.id
            GROUP BY s.id
            ORDER BY s.performed_on DESC, s.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return {
        "volume_history": [dict(row) for row in volume_rows],
        "best_lifts": [{**dict(row), "estimated_1rm": round(row["estimated_1rm"], 1)} for row in best_rows],
        "recent_sessions": [dict(row) for row in recent_sessions],
    }


def research_items() -> list[dict[str, str]]:
    return [
        {
            "title": "ACSM Progression Models in Resistance Training for Healthy Adults",
            "summary": "근력 향상은 높은 강도와 낮은 반복수, 근비대는 중간 반복수와 점진적 과부하가 핵심이라는 원칙을 기본 루틴에 반영했습니다.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/19204579/",
        },
        {
            "title": "Load and Volume Autoregulation Meta-analysis",
            "summary": "직전 수행 결과를 기준으로 다음 중량을 조절하는 접근이 유효할 수 있어 권장 중량 로직에 반영했습니다.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/35038063/",
        },
    ]


def render_research_cards() -> str:
    return "".join(
        f"""
        <article class="research-card">
          <strong>{html.escape(item["title"])}</strong>
          <p>{html.escape(item["summary"])}</p>
          <a href="{html.escape(item["url"])}" target="_blank" rel="noreferrer">원문 보기</a>
        </article>
        """
        for item in research_items()
    )


def render_page(page: str, notice: str = "", logger_day_name: Optional[str] = None) -> str:
    pages = {
        "home": render_home_page,
        "planner": render_planner_page,
        "atlas": render_atlas_page,
        "logger": lambda notice="": render_logger_page(logger_day_name=logger_day_name, notice=notice),
        "progress": render_progress_page,
    }
    if page not in pages:
        raise HTTPException(status_code=404, detail="Page not found")
    return pages[page](notice=notice)


def render_notice(notice: str) -> str:
    if not notice:
        return ""
    return f'<div class="notice-banner">{html.escape(notice)}</div>'


def render_home_page(notice: str = "") -> str:
    return f"""
    <section class="page-fragment" data-page="home">
      {render_notice(notice)}
      <header class="hero">
        <div>
          <p class="eyebrow">짐핏</p>
          <h1>짐핏</h1>
          <p class="hero-copy">계획, 도감, 기록, 성장을 분리해 집중도를 높인 HTMX 기반 웨이트 관리 앱입니다.</p>
        </div>
        <div class="hero-card glass">
          <div class="metric"><span>컨셉</span><strong>한 번에 하나의 화면만</strong></div>
          <div class="metric"><span>원칙</span><strong>주간 루틴과 점진적 과부하</strong></div>
          <div class="metric"><span>기록</span><strong>세트별 무게와 반복수 누적</strong></div>
        </div>
      </header>
      <section class="panel glass intro-panel">
        <div class="section-head">
          <div><p class="eyebrow">Concept</p><h2>앱 개요와 설계 원칙</h2></div>
        </div>
        <div class="intro-grid">
          <article class="concept-card"><strong>루틴 설계 우선</strong><p class="muted">기록 전에 분할과 종목을 먼저 설계하고 수정합니다.</p></article>
          <article class="concept-card"><strong>주간 구조 고정</strong><p class="muted">모든 루틴은 1주 단위로 관리되며 2분할과 3분할을 지원합니다.</p></article>
          <article class="concept-card"><strong>근거 기반 세트</strong><p class="muted">스트렝스 4세트, 근비대 3세트, 보조운동 고반복 원칙을 유지합니다.</p></article>
        </div>
      </section>
      <section class="icon-grid">
        <button class="icon-panel glass" hx-get="/ui/page/planner" hx-target="#page-shell" hx-swap="innerHTML"><span class="icon-badge">􀉊</span><strong>분할 선택 / 루틴 편집</strong><p class="muted">분할 생성 후 종목, 세트, 횟수, 중량을 수정합니다.</p></button>
        <button class="icon-panel glass" hx-get="/ui/page/atlas" hx-target="#page-shell" hx-swap="innerHTML"><span class="icon-badge">􀋦</span><strong>운동 도감</strong><p class="muted">운동명, 한글 설명, 부위, 장비와 통일된 이미지를 확인합니다.</p></button>
        <button class="icon-panel glass" hx-get="/ui/page/logger" hx-target="#page-shell" hx-swap="innerHTML"><span class="icon-badge">􀐫</span><strong>수행 기록</strong><p class="muted">세트별 무게와 반복수를 저장합니다.</p></button>
        <button class="icon-panel glass" hx-get="/ui/page/progress" hx-target="#page-shell" hx-swap="innerHTML"><span class="icon-badge">􀑪</span><strong>성장 추이</strong><p class="muted">볼륨, 최고중량, 추정 1RM 변화를 확인합니다.</p></button>
      </section>
      <section class="panel glass">
        <div class="section-head">
          <div><p class="eyebrow">Evidence</p><h2>루틴 설계 근거</h2></div>
        </div>
        <div class="research-notes">{render_research_cards()}</div>
      </section>
    </section>
    """


def render_split_cards(active_split: Optional[str]) -> str:
    cards = []
    for key, split in SPLIT_DEFINITIONS.items():
        active_class = " active" if active_split == key else ""
        label = "Balanced" if key == "2-day" else "Focused"
        cards.append(
            f"""
            <form hx-post="/ui/routines/generate" hx-target="#page-shell" hx-swap="innerHTML">
              <input type="hidden" name="split_type" value="{key}" />
              <button class="split-card{active_class}" type="submit">
                <span class="split-label">{label}</span>
                <strong class="split-title">{html.escape(split["label"])}</strong>
                <small class="split-desc">{html.escape(split["description"])}</small>
              </button>
            </form>
            """
        )
    return "".join(cards)


def render_exercise_options(selected_id: int) -> str:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for exercise in get_exercises_payload():
        grouped.setdefault(exercise["muscle_group_label"], []).append(exercise)
    parts = []
    for group in sorted(grouped.keys()):
        options = "".join(
            f"""
            <option value="{item["id"]}" {"selected" if item["id"] == selected_id else ""}
              data-name="{html.escape(item["name"])}"
              data-group="{html.escape(item["muscle_group_label"])}"
              data-equipment="{html.escape(item["equipment_label"])}"
              data-description="{html.escape(item["description"])}">{html.escape(item["name"])}</option>
            """
            for item in grouped[group]
        )
        parts.append(f'<optgroup label="{html.escape(group)}">{options}</optgroup>')
    return "".join(parts)


def render_routine_editor(routine_data: Optional[dict[str, Any]]) -> str:
    if not routine_data:
        return '<div class="routine-editor empty-state">분할을 선택하면 기본 루틴이 생성됩니다.</div>'
    hidden_split = html.escape(routine_data["routine"]["split_type"])
    days_html = []
    for day_name, items in routine_data["days"].items():
        rows = []
        for item in items:
            rows.append(
                f"""
                <div class="routine-item" data-role="{html.escape(item["role"])}">
                  <input type="hidden" name="id" value="{item["id"]}" />
                  <input type="hidden" name="day_name" value="{html.escape(day_name)}" />
                  <input type="hidden" name="day_order" value="{item["day_order"]}" />
                  <input type="hidden" name="focus" value="{html.escape(item["focus"])}" />
                  <input type="hidden" name="role" value="{html.escape(item["role"])}" />
                  <input type="hidden" name="notes" value="{html.escape(item["notes"])}" />
                  <div>
                    <select class="field exercise-select" name="exercise_id">
                      {render_exercise_options(item["exercise_id"])}
                    </select>
                    <div class="routine-summary">
                      <strong class="exercise-name">{html.escape(item["name"])}</strong>
                      <div class="muted exercise-meta-line">{html.escape(item["muscle_group_label"])} · {html.escape(MOVEMENT_LABELS.get(item["role"], item["role"]))} · {html.escape(item["equipment_label"])}</div>
                      <div class="muted exercise-description">{html.escape(item["description"])}</div>
                    </div>
                  </div>
                  <input value="{item["set_count"]}" type="number" min="1" name="set_count" />
                  <input value="{html.escape(item["rep_range"])}" type="text" name="rep_range" />
                  <input value="{item["target_weight"] or ''}" type="number" min="0" step="0.5" name="target_weight" />
                </div>
                """
            )
        days_html.append(
            f"""
            <section class="routine-day">
              <h3>{html.escape(day_name)}</h3>
              <p class="muted">{html.escape(items[0]["focus"])}</p>
              {''.join(rows)}
            </section>
            """
        )
    return f"""
    <form class="routine-editor" hx-post="/ui/routines/save" hx-target="#page-shell" hx-swap="innerHTML">
      <input type="hidden" name="split_type" value="{hidden_split}" />
      {''.join(days_html)}
      <div class="sticky-actions"><button class="button secondary" type="submit">루틴 저장</button></div>
    </form>
    """


def render_planner_page(notice: str = "") -> str:
    routine_data = fetch_routine_payload()
    active_split = routine_data["routine"]["split_type"] if routine_data else None
    return f"""
    <section class="page-fragment" data-page="planner">
      {render_notice(notice)}
      <div class="page-header">
        <div><p class="eyebrow">Planner</p><h2>분할 선택과 루틴 편집</h2></div>
      </div>
      <div class="page-grid">
        <section class="panel glass">
          <div class="section-head"><div><p class="eyebrow">Step 1</p><h2>분할 선택</h2></div></div>
          <div class="split-options">{render_split_cards(active_split)}</div>
        </section>
        <section class="panel glass">
          <div class="section-head"><div><p class="eyebrow">Step 2</p><h2>루틴 편집</h2></div></div>
          {render_routine_editor(routine_data)}
        </section>
      </div>
    </section>
    """


def render_atlas_page(notice: str = "") -> str:
    cards = []
    for exercise in get_exercises_payload():
        cards.append(
            f"""
            <article class="catalog-card">
              <div class="catalog-art"><img src="{exercise_artwork_path(exercise)}" alt="{html.escape(exercise["name"])}" /></div>
              <div>
                <strong>{html.escape(exercise["name"])}</strong>
                <p class="exercise-meta">{html.escape(exercise["muscle_group_label"])} · {html.escape(exercise["secondary_group_label"])} · {html.escape(exercise["equipment_label"])}</p>
                <p class="exercise-meta">{html.escape(exercise["description"])}</p>
                <div><span class="badge">{html.escape(exercise["movement_type_label"])}</span><span class="badge">{html.escape(exercise["laterality_label"])}</span></div>
              </div>
            </article>
            """
        )
    return f"""
    <section class="page-fragment" data-page="atlas">
      {render_notice(notice)}
      <div class="page-header"><div><p class="eyebrow">Atlas</p><h2>운동 도감</h2></div></div>
      <section class="panel glass">
        <div class="catalog">{''.join(cards)}</div>
        <p class="muted">이미지 소스: 오픈소스 SVG 아이콘 세트 Tabler, Lucide, Health Icons</p>
      </section>
    </section>
    """


def recommended_text(exercise_id: int) -> str:
    with closing(get_connection()) as conn:
        exercise = conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
        routine = get_active_routine(conn)
        routine_entry = None
        if routine:
            routine_entry = conn.execute(
                "SELECT * FROM routine_days WHERE routine_id = ? AND exercise_id = ? ORDER BY id DESC LIMIT 1",
                (routine["id"], exercise_id),
            ).fetchone()
        recommendation = recommend_next_weight(exercise, routine_entry, load_latest_exercise_performance(conn, exercise_id))
    return f'{recommendation["recommended_weight"]}kg · {recommendation["reason"]}'


def render_logger_page(logger_day_name: Optional[str] = None, notice: str = "") -> str:
    routine_data = fetch_routine_payload()
    if not routine_data or not routine_data["days"]:
        body = '<div class="log-form empty-state">먼저 루틴 화면에서 분할을 선택해 루틴을 생성하세요.</div>'
    else:
        day_names = list(routine_data["days"].keys())
        selected_day = logger_day_name if logger_day_name in routine_data["days"] else day_names[0]
        options = "".join(
            f'<option value="{html.escape(day)}" {"selected" if day == selected_day else ""}>{html.escape(day)}</option>'
            for day in day_names
        )
        rows = []
        for item in routine_data["days"][selected_day]:
            rows.append(
                f"""
                <article class="log-card">
                  <input type="hidden" name="exercise_id" value="{item["exercise_id"]}" />
                  <strong>{html.escape(item["name"])}</strong>
                  <p class="muted">{html.escape(MOVEMENT_LABELS.get(item["role"], item["role"]))} · 추천 {html.escape(recommended_text(item["exercise_id"]))}</p>
                  <div class="log-row">
                    <input type="number" min="0" step="0.5" placeholder="무게(kg)" name="weight" value="{item["target_weight"] or ''}" />
                    <input type="number" min="1" placeholder="반복 수" name="reps" />
                    <input type="number" min="1" max="{item["set_count"]}" placeholder="세트 번호" name="set_number" />
                    <input type="text" placeholder="세트 타입" name="set_type" value="{html.escape(item["role"])}" />
                  </div>
                </article>
                """
            )
        body = f"""
        <form class="log-form" hx-post="/ui/workouts/log" hx-target="#page-shell" hx-swap="innerHTML">
          <input type="hidden" name="split_type" value="{html.escape(routine_data["routine"]["split_type"])}" />
          <div class="log-meta">
            <input class="field" type="date" name="performed_on" value="{date.today().isoformat()}" />
            <select class="field" name="day_name" hx-get="/ui/page/logger" hx-target="#page-shell" hx-swap="innerHTML" hx-include="[name='performed_on']">
              {options}
            </select>
          </div>
          <div class="log-grid">{''.join(rows)}</div>
          <div class="sticky-actions"><button class="button" type="submit">기록 저장</button></div>
        </form>
        """
    return f"""
    <section class="page-fragment" data-page="logger">
      {render_notice(notice)}
      <div class="page-header"><div><p class="eyebrow">Logger</p><h2>수행 기록</h2></div></div>
      <section class="panel glass">{body}</section>
    </section>
    """


def render_progress_page(notice: str = "") -> str:
    progress = get_progress_payload()
    if not progress["best_lifts"] and not progress["recent_sessions"]:
        body = '<div class="progress-board empty-state">운동 기록을 쌓으면 볼륨과 추정 1RM이 표시됩니다.</div>'
    else:
        total_volume = round(sum(item["volume"] for item in progress["volume_history"]))
        sessions = len(progress["recent_sessions"])
        best = progress["best_lifts"][0] if progress["best_lifts"] else None
        body = f"""
        <div class="progress-board">
          <div class="stats-grid">
            <div class="progress-card"><span class="muted">누적 표시 볼륨</span><strong>{total_volume:,} kg</strong></div>
            <div class="progress-card"><span class="muted">최근 세션 수</span><strong>{sessions}</strong></div>
            <div class="progress-card"><span class="muted">최고 추정 1RM</span><strong>{f"{best['estimated_1rm']} kg" if best else "-"}</strong></div>
          </div>
          <div class="progress-card"><h3>Best Lifts</h3><div class="lift-list">{
            ''.join(f'<div class="session-card"><strong>{html.escape(item["name"])}</strong><div class="muted">{html.escape(MUSCLE_LABELS.get(item["muscle_group"], item["muscle_group"]))} · 최고중량 {item["max_weight"]}kg · 추정 1RM {item["estimated_1rm"]}kg</div></div>' for item in progress["best_lifts"])
          }</div></div>
          <div class="progress-card"><h3>Recent Sessions</h3><div class="session-list">{
            ''.join(f'<div class="session-card"><strong>{html.escape(item["performed_on"])}</strong><div class="muted">{html.escape(item["day_name"])} · {item["sets_logged"]}세트 기록</div></div>' for item in progress["recent_sessions"])
          }</div></div>
        </div>
        """
    return f"""
    <section class="page-fragment" data-page="progress">
      {render_notice(notice)}
      <div class="page-header"><div><p class="eyebrow">Progress</p><h2>성장 추이</h2></div></div>
      <section class="panel glass">{body}</section>
    </section>
    """


app = FastAPI(title="Workout Manager")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/ui/page/{page_name}", response_class=HTMLResponse)
def get_ui_page(page_name: str, day_name: Optional[str] = None) -> str:
    return render_page(page_name, logger_day_name=day_name)


@app.post("/ui/routines/generate", response_class=HTMLResponse)
def generate_routine_fragment(split_type: str = Form(...)) -> str:
    with closing(get_connection()) as conn:
        days = build_default_routine(split_type, conn)
    create_or_replace_routine(split_type, days)
    return render_planner_page(notice=f"{SPLIT_DEFINITIONS[split_type]['label']} 기본 루틴을 생성했습니다.")


@app.post("/ui/routines/save", response_class=HTMLResponse)
async def save_routine_fragment(request: Request) -> str:
    form = await request.form()
    split_type = str(form.get("split_type"))
    ids = form.getlist("id")
    day_names = form.getlist("day_name")
    day_orders = form.getlist("day_order")
    focuses = form.getlist("focus")
    exercise_ids = form.getlist("exercise_id")
    roles = form.getlist("role")
    set_counts = form.getlist("set_count")
    rep_ranges = form.getlist("rep_range")
    notes = form.getlist("notes")
    target_weights = form.getlist("target_weight")

    days = []
    for index in range(len(exercise_ids)):
        weight_value = str(target_weights[index]).strip()
        days.append(
            {
                "id": int(ids[index]) if str(ids[index]).strip() else None,
                "day_name": str(day_names[index]),
                "day_order": int(day_orders[index]),
                "focus": str(focuses[index]),
                "exercise_id": int(exercise_ids[index]),
                "role": str(roles[index]),
                "set_count": int(set_counts[index]),
                "rep_range": str(rep_ranges[index]),
                "notes": str(notes[index]),
                "target_weight": float(weight_value) if weight_value else None,
            }
        )
    create_or_replace_routine(split_type, days)
    return render_planner_page(notice="루틴 편집 내용을 저장했습니다.")


@app.post("/ui/workouts/log", response_class=HTMLResponse)
async def log_workout_fragment(request: Request) -> str:
    form = await request.form()
    performed_on = date.fromisoformat(str(form.get("performed_on")))
    split_type = str(form.get("split_type"))
    day_name = str(form.get("day_name"))
    exercise_ids = form.getlist("exercise_id")
    weights = form.getlist("weight")
    reps_list = form.getlist("reps")
    set_numbers = form.getlist("set_number")
    set_types = form.getlist("set_type")

    entries = []
    for index in range(len(exercise_ids)):
        weight_value = str(weights[index]).strip()
        reps_value = str(reps_list[index]).strip()
        set_number_value = str(set_numbers[index]).strip()
        if not (weight_value and reps_value and set_number_value):
            continue
        entries.append(
            {
                "exercise_id": int(exercise_ids[index]),
                "set_type": str(set_types[index] or "working"),
                "set_number": int(set_number_value),
                "weight": float(weight_value),
                "reps": int(reps_value),
                "notes": "",
            }
        )

    if not entries:
        return render_logger_page(logger_day_name=day_name, notice="최소 1개 세트 기록이 필요합니다.")

    with closing(get_connection()) as conn:
        session_cursor = conn.execute(
            """
            INSERT INTO workout_sessions (performed_on, split_type, day_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (performed_on.isoformat(), split_type, day_name, datetime.now().isoformat(timespec="seconds")),
        )
        session_id = session_cursor.lastrowid
        conn.executemany(
            """
            INSERT INTO workout_sets (session_id, exercise_id, set_type, set_number, weight, reps, notes)
            VALUES (:session_id, :exercise_id, :set_type, :set_number, :weight, :reps, :notes)
            """,
            [{**entry, "session_id": session_id} for entry in entries],
        )
        conn.commit()
    return render_progress_page(notice=f"{day_name} 기록 {len(entries)}세트를 저장했습니다.")


@app.get("/api/splits")
def get_splits() -> dict[str, Any]:
    return {"splits": SPLIT_DEFINITIONS}


@app.get("/api/exercises")
def get_exercises(group: Optional[str] = None) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        if group:
            rows = conn.execute(
                "SELECT * FROM exercises WHERE muscle_group = ? ORDER BY name",
                (group,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM exercises ORDER BY muscle_group, name").fetchall()
        return {"items": [enrich_exercise_payload(row) for row in rows]}


@app.get("/api/exercises/{exercise_id}/illustration.svg")
def get_exercise_illustration(exercise_id: int) -> Response:
    with closing(get_connection()) as conn:
        exercise = conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        primary, accent = MUSCLE_COLORS.get(exercise["muscle_group"], ("#0f172a", "#e2e8f0"))
        label = MUSCLE_LABELS.get(exercise["muscle_group"], exercise["muscle_group"])[:8]
        svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="240" height="160" viewBox="0 0 240 160" fill="none">
          <rect width="240" height="160" rx="28" fill="{accent}"/>
          <circle cx="120" cy="38" r="16" fill="{primary}" opacity="0.85"/>
          <rect x="96" y="58" width="48" height="54" rx="18" fill="{primary}" opacity="0.85"/>
          <rect x="68" y="60" width="22" height="48" rx="11" fill="{primary}" opacity="0.65"/>
          <rect x="150" y="60" width="22" height="48" rx="11" fill="{primary}" opacity="0.65"/>
          <rect x="98" y="110" width="16" height="34" rx="8" fill="{primary}" opacity="0.75"/>
          <rect x="126" y="110" width="16" height="34" rx="8" fill="{primary}" opacity="0.75"/>
          <text x="120" y="147" text-anchor="middle" fill="#0f172a" font-family="Arial, sans-serif" font-size="16" font-weight="700">{label}</text>
        </svg>
        """.strip()
        return Response(content=svg, media_type="image/svg+xml")


@app.post("/api/routines/generate")
def generate_routine(payload: RoutineGenerateRequest) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        days = build_default_routine(payload.split_type, conn)
    routine_id = create_or_replace_routine(payload.split_type, days)
    return {"routine_id": routine_id, "data": fetch_routine_payload()}


@app.get("/api/routines/current")
def get_current_routine() -> dict[str, Any]:
    data = fetch_routine_payload()
    return {"data": data}


@app.put("/api/routines/current")
def update_current_routine(payload: RoutineUpdateRequest) -> dict[str, Any]:
    days = [item.model_dump() for item in payload.days]
    routine_id = create_or_replace_routine(payload.split_type, days)
    return {"routine_id": routine_id, "data": fetch_routine_payload()}


@app.post("/api/workouts/log")
def log_workout(payload: WorkoutLogRequest) -> dict[str, Any]:
    try:
        performed_on = date.fromisoformat(payload.performed_on)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc
    with closing(get_connection()) as conn:
        session_cursor = conn.execute(
            """
            INSERT INTO workout_sessions (performed_on, split_type, day_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                performed_on.isoformat(),
                payload.split_type,
                payload.day_name,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        session_id = session_cursor.lastrowid
        conn.executemany(
            """
            INSERT INTO workout_sets (session_id, exercise_id, set_type, set_number, weight, reps, notes)
            VALUES (:session_id, :exercise_id, :set_type, :set_number, :weight, :reps, :notes)
            """,
            [{**entry.model_dump(), "session_id": session_id} for entry in payload.entries],
        )
        conn.commit()
        return {"session_id": session_id, "logged_sets": len(payload.entries)}


@app.get("/api/progress/overview")
def get_progress_overview(limit: int = Query(default=12, ge=1, le=52)) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        volume_rows = conn.execute(
            """
            SELECT e.muscle_group, s.performed_on, ROUND(SUM(ws.weight * ws.reps), 1) AS volume
            FROM workout_sets ws
            JOIN exercises e ON e.id = ws.exercise_id
            JOIN workout_sessions s ON s.id = ws.session_id
            GROUP BY e.muscle_group, s.performed_on
            ORDER BY s.performed_on DESC
            LIMIT ?
            """,
            (limit * 6,),
        ).fetchall()
        best_rows = conn.execute(
            """
            SELECT e.name, e.muscle_group, MAX(ws.weight) AS max_weight, MAX((ws.weight * (1 + (ws.reps / 30.0)))) AS estimated_1rm
            FROM workout_sets ws
            JOIN exercises e ON e.id = ws.exercise_id
            GROUP BY e.id
            ORDER BY estimated_1rm DESC
            LIMIT 12
            """
        ).fetchall()
        recent_sessions = conn.execute(
            """
            SELECT s.performed_on, s.day_name, COUNT(ws.id) AS sets_logged
            FROM workout_sessions s
            LEFT JOIN workout_sets ws ON ws.session_id = s.id
            GROUP BY s.id
            ORDER BY s.performed_on DESC, s.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return {
            "volume_history": [dict(row) for row in volume_rows],
            "best_lifts": [
                {**dict(row), "estimated_1rm": round(row["estimated_1rm"], 1)} for row in best_rows
            ],
            "recent_sessions": [dict(row) for row in recent_sessions],
        }


@app.get("/api/recommendations/next")
def get_next_recommendation(exercise_id: int) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        exercise = conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        routine = get_active_routine(conn)
        routine_entry = None
        if routine:
            routine_entry = conn.execute(
                """
                SELECT * FROM routine_days
                WHERE routine_id = ? AND exercise_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (routine["id"], exercise_id),
            ).fetchone()
        latest_sets = load_latest_exercise_performance(conn, exercise_id)
        recommendation = recommend_next_weight(exercise, routine_entry, latest_sets)
        return {
            "exercise": enrich_exercise_payload(exercise),
            "latest_sets": [dict(row) for row in latest_sets],
            "recommendation": recommendation,
        }


@app.get("/api/research")
def get_research_notes() -> dict[str, Any]:
    return {
        "items": [
            {
                "title": "ACSM Progression Models in Resistance Training for Healthy Adults",
                "summary": "근력 향상은 상대적으로 높은 강도와 낮은 반복수, 근비대는 중간 반복수와 점진적 과부하가 핵심이라는 원칙을 루틴 기본값에 반영했습니다.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/19204579/",
            },
            {
                "title": "Load and Volume Autoregulation Meta-analysis",
                "summary": "고정 퍼센트보다 수행 결과를 바탕으로 다음 중량을 조절하는 접근이 유효할 수 있어, 직전 기록 기반 권장 중량 로직을 넣었습니다.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/35038063/",
            },
        ]
    }
