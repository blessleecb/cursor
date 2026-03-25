from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
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
    {"slug": "barbell-bench-press", "name": "Barbell Bench Press", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "incline-dumbbell-press", "name": "Incline Dumbbell Press", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 0},
    {"slug": "machine-chest-press", "name": "Machine Chest Press", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "cable-fly", "name": "Cable Fly", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "push-up", "name": "Push-Up", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "weighted-dip", "name": "Weighted Dip", "muscle_group": "chest", "secondary_group": "triceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "pull-up", "name": "Pull-Up", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "weighted-pull-up", "name": "Weighted Pull-Up", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "strength", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "barbell-row", "name": "Barbell Row", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "chest-supported-row", "name": "Chest-Supported Row", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "lat-pulldown", "name": "Lat Pulldown", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "single-arm-cable-row", "name": "Single Arm Cable Row", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "deadlift", "name": "Deadlift", "muscle_group": "legs", "secondary_group": "back", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "back-squat", "name": "Back Squat", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "front-squat", "name": "Front Squat", "muscle_group": "legs", "secondary_group": "core", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "leg-press", "name": "Leg Press", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "romanian-deadlift", "name": "Romanian Deadlift", "muscle_group": "hamstrings", "secondary_group": "glutes", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "lying-leg-curl", "name": "Lying Leg Curl", "muscle_group": "hamstrings", "secondary_group": "calves", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "bulgarian-split-squat", "name": "Bulgarian Split Squat", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "walking-lunge", "name": "Walking Lunge", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "barbell-overhead-press", "name": "Barbell Overhead Press", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "seated-dumbbell-press", "name": "Seated Dumbbell Press", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 0},
    {"slug": "machine-shoulder-press", "name": "Machine Shoulder Press", "muscle_group": "shoulders", "secondary_group": "triceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "lateral-raise", "name": "Lateral Raise", "muscle_group": "side delts", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "cable-lateral-raise", "name": "Cable Lateral Raise", "muscle_group": "side delts", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "rear-delt-fly", "name": "Rear Delt Fly", "muscle_group": "rear delts", "secondary_group": "upper back", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "face-pull", "name": "Face Pull", "muscle_group": "rear delts", "secondary_group": "upper back", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "upright-row", "name": "Upright Row", "muscle_group": "side delts", "secondary_group": "traps", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "barbell-curl", "name": "Barbell Curl", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "incline-dumbbell-curl", "name": "Incline Dumbbell Curl", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "hammer-curl", "name": "Hammer Curl", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "dumbbell", "is_unilateral": 1},
    {"slug": "cable-curl", "name": "Cable Curl", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "ez-bar-curl", "name": "EZ Bar Curl", "muscle_group": "biceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "close-grip-bench-press", "name": "Close Grip Bench Press", "muscle_group": "triceps", "secondary_group": "chest", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "cable-pushdown", "name": "Cable Pushdown", "muscle_group": "triceps", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "overhead-triceps-extension", "name": "Overhead Triceps Extension", "muscle_group": "triceps", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 0},
    {"slug": "skull-crusher", "name": "Skull Crusher", "muscle_group": "triceps", "secondary_group": "forearms", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "single-arm-pushdown", "name": "Single Arm Pushdown", "muscle_group": "triceps", "secondary_group": "shoulders", "movement_type": "hypertrophy", "equipment": "cable", "is_unilateral": 1},
    {"slug": "standing-calf-raise", "name": "Standing Calf Raise", "muscle_group": "calves", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "seated-calf-raise", "name": "Seated Calf Raise", "muscle_group": "calves", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "hip-thrust", "name": "Hip Thrust", "muscle_group": "glutes", "secondary_group": "hamstrings", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "glute-bridge", "name": "Glute Bridge", "muscle_group": "glutes", "secondary_group": "hamstrings", "movement_type": "hypertrophy", "equipment": "bodyweight", "is_unilateral": 0},
    {"slug": "leg-extension", "name": "Leg Extension", "muscle_group": "legs", "secondary_group": "quads", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "hack-squat", "name": "Hack Squat", "muscle_group": "legs", "secondary_group": "glutes", "movement_type": "strength", "equipment": "machine", "is_unilateral": 0},
    {"slug": "good-morning", "name": "Good Morning", "muscle_group": "hamstrings", "secondary_group": "back", "movement_type": "strength", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "t-bar-row", "name": "T-Bar Row", "muscle_group": "back", "secondary_group": "rear delts", "movement_type": "hypertrophy", "equipment": "barbell", "is_unilateral": 0},
    {"slug": "machine-row", "name": "Machine Row", "muscle_group": "back", "secondary_group": "biceps", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
    {"slug": "pec-deck", "name": "Pec Deck", "muscle_group": "chest", "secondary_group": "front delts", "movement_type": "hypertrophy", "equipment": "machine", "is_unilateral": 0},
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
        conn.commit()


def seed_exercises() -> None:
    with closing(get_connection()) as conn:
        existing = conn.execute("SELECT COUNT(*) AS count FROM exercises").fetchone()["count"]
        if existing:
            return
        conn.executemany(
            """
            INSERT INTO exercises
            (slug, name, muscle_group, secondary_group, movement_type, equipment, is_unilateral)
            VALUES (:slug, :name, :muscle_group, :secondary_group, :movement_type, :equipment, :is_unilateral)
            """,
            EXERCISES,
        )
        conn.commit()


def fetch_exercise_map(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    rows = conn.execute("SELECT * FROM exercises").fetchall()
    return {row["slug"]: row for row in rows}


def default_targets(role: str) -> SetTargets:
    if role == "strength":
        return SetTargets(4, "warm-up 8 / top 4-6 / top 4-6 / back-off 6-8")
    if role == "hypertrophy":
        return SetTargets(3, "8-12")
    return SetTargets(3, "12-20")


def suggest_initial_weight(exercise_name: str, role: str) -> float:
    base = 20.0
    name = exercise_name.lower()
    if "squat" in name or "deadlift" in name or "leg press" in name:
        base = 60.0
    elif "row" in name or "press" in name or "pull-up" in name:
        base = 40.0
    elif "curl" in name or "raise" in name or "pushdown" in name:
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
                            "notes": f"{group} {role} priority",
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
                    "notes": f"{accessory_group} accessory",
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
            SELECT rd.*, e.name, e.slug, e.muscle_group, e.secondary_group, e.equipment
            FROM routine_days rd
            JOIN exercises e ON e.id = rd.exercise_id
            WHERE rd.routine_id = ?
            ORDER BY rd.day_order, rd.role, rd.id
            """,
            (routine["id"],),
        ).fetchall()
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["day_name"], []).append(dict(row))
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
        return {"items": [dict(row) for row in rows]}


@app.get("/api/exercises/{exercise_id}/illustration.svg")
def get_exercise_illustration(exercise_id: int) -> Response:
    with closing(get_connection()) as conn:
        exercise = conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        primary, accent = MUSCLE_COLORS.get(exercise["muscle_group"], ("#0f172a", "#e2e8f0"))
        label = exercise["muscle_group"].upper()[:10]
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
            "exercise": dict(exercise),
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
