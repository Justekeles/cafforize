from flask import Blueprint, jsonify, render_template, request

from . import db

bp = Blueprint("main", __name__)


def _round_spoons(value: float) -> float:
    # Round to the nearest quarter spoon -- that's about as precise as a
    # spoon of coffee grounds gets in real life.
    return round(value * 4) / 4


@bp.get("/")
def index():
    return render_template(
        "index.html",
        default_water=db.DEFAULT_WATER,
        default_spoons=db.DEFAULT_SPOONS,
    )


@bp.get("/api/suggestion")
def suggestion():
    try:
        water = float(request.args.get("water", db.DEFAULT_WATER))
    except (TypeError, ValueError):
        return jsonify(error="Invalid water amount"), 400
    if water <= 0:
        return jsonify(error="Water amount must be greater than zero"), 400

    best = db.get_best_ratio()
    spoons = _round_spoons(water * best["ratio"])
    return jsonify(
        water=water,
        spoons=spoons,
        ratio=best["ratio"],
        source=best["source"],
        avg_grade=best["avg_grade"],
        sample_size=best["sample_size"],
    )


@bp.post("/api/brews")
def create_brew():
    payload = request.get_json(silent=True) or {}
    try:
        water = float(payload.get("water"))
        spoons = float(payload.get("spoons"))
    except (TypeError, ValueError):
        return jsonify(error="water and spoons must be numbers"), 400
    if water <= 0 or spoons <= 0:
        return jsonify(error="water and spoons must be greater than zero"), 400

    brew_id = db.add_brew(water, spoons)
    return jsonify(id=brew_id), 201


@bp.get("/api/brews")
def list_brews():
    return jsonify(history=db.get_history())


@bp.post("/api/brews/<int:brew_id>/grade")
def grade_brew(brew_id):
    payload = request.get_json(silent=True) or {}
    try:
        grade = int(payload.get("grade"))
    except (TypeError, ValueError):
        return jsonify(error="grade must be an integer 1-5"), 400
    if grade < 1 or grade > 5:
        return jsonify(error="grade must be between 1 and 5"), 400

    if not db.grade_brew(brew_id, grade):
        return jsonify(error="brew not found"), 404
    return jsonify(ok=True)


@bp.delete("/api/brews/<int:brew_id>")
def remove_brew(brew_id):
    if not db.delete_brew(brew_id):
        return jsonify(error="brew not found"), 404
    return jsonify(ok=True)
