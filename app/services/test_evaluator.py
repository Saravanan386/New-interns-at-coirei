# app/services/test_evaluator.py

import re
from rapidfuzz import fuzz
from app.models.test import Option


def evaluate_mcq(question, selected_option):
    if not selected_option:
        return 0
    if selected_option.is_correct:
        return question.marks
    return 0


def evaluate_checkbox(question, selected_ids):
    # Partial marks supported.
    if not selected_ids:
        return 0

    correct_ids = {
        option.id 
        for option in question.options 
        if option.is_correct
    }
    selected_ids = set(selected_ids)
    matched = len(correct_ids.intersection(selected_ids))

    if len(correct_ids) == 0:
        return 0

    score = (matched / len(correct_ids)) * question.marks
    return round(score, 2)


def evaluate_short_answer(expected_answer, student_answer, marks):
    # Fuzzy text matching.
    if not student_answer:
        return 0

    similarity = fuzz.ratio(expected_answer.lower(), student_answer.lower())
    score = (similarity / 100) * marks
    return round(score, 2)


def evaluate_long_answer(expected_answer, student_answer, marks):
    # Keyword matching.
    if not student_answer:
        return 0

    keywords = set(re.findall(r"\w+", expected_answer.lower()))
    student_words = set(re.findall(r"\w+", student_answer.lower()))
    matched = len(keywords.intersection(student_words))

    if len(keywords) == 0:
        return 0

    score = (matched / len(keywords)) * marks
    return round(score, 2)


def evaluate_question(db, question, answer):
    if question.question_type == "mcq":
        option = None
        if answer.selected_option_id:
            option = (
                db.query(Option)
                .filter(Option.id == answer.selected_option_id)
                .first()
            )
        return evaluate_mcq(question, option)

    if question.question_type == "checkbox":
        return evaluate_checkbox(question, answer.selected_option_ids or [])

    if question.question_type == "short_answer":
        return evaluate_short_answer(
            question.expected_answer or "",
            answer.text_answer or "",
            question.marks,
        )

    if question.question_type == "long_answer":
        return evaluate_long_answer(
            question.expected_answer or "",
            answer.text_answer or "",
            question.marks,
        )

    return 0