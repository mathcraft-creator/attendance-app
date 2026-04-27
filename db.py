from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Tuple

DB_PATH = Path("questions.db")

MATERIAL_COLUMNS = [
    "question_id",
    "grade",
    "school_level",
    "unit",
    "sub_type",
    "difficulty",
    "question_text",
    "answer",
    "solution",
    "source",
]


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_filename TEXT NOT NULL,
                question_number TEXT NOT NULL,
                question_text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS academy_questions (
                question_id TEXT PRIMARY KEY,
                grade TEXT NOT NULL,
                school_level TEXT NOT NULL,
                unit TEXT NOT NULL,
                sub_type TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_text TEXT NOT NULL,
                answer TEXT NOT NULL,
                solution TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_questions(
    source_filename: str,
    questions: Iterable[Tuple[str, str]],
    db_path: Path = DB_PATH,
) -> int:
    rows = [(source_filename, number, text) for number, text in questions]
    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO questions (source_filename, question_number, question_text)
            VALUES (?, ?, ?)
            """,
            rows,
        )
        conn.commit()
    return len(rows)


def save_academy_questions(
    rows: Iterable[Mapping[str, str]],
    db_path: Path = DB_PATH,
) -> int:
    payload = [
        tuple((row.get(column, "") or "").strip() for column in MATERIAL_COLUMNS)
        for row in rows
    ]
    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO academy_questions (
                question_id, grade, school_level, unit, sub_type,
                difficulty, question_text, answer, solution, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
                grade = excluded.grade,
                school_level = excluded.school_level,
                unit = excluded.unit,
                sub_type = excluded.sub_type,
                difficulty = excluded.difficulty,
                question_text = excluded.question_text,
                answer = excluded.answer,
                solution = excluded.solution,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
            """,
            payload,
        )
        conn.commit()
    return len(payload)


def get_academy_questions(db_path: Path = DB_PATH) -> list[dict[str, str]]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                question_id, grade, school_level, unit, sub_type,
                difficulty, question_text, answer, solution, source
            FROM academy_questions
            """
        ).fetchall()

    return [dict(row) for row in rows]
