import os
from datetime import datetime, timezone
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

load_dotenv(Path(__file__).parent.parent / ".flaskenv", override=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# Default values for database connection
db_user = os.environ.get("POSTGRES_USER", "tavern")
db_password = os.environ.get("POSTGRES_PASSWORD", "tavern")
db_host = os.environ.get("POSTGRES_HOST", "db")
db_port = os.environ.get("POSTGRES_PORT", "5432")
db_name = os.environ.get("POSTGRES_DB", "tavern_board")

# Check if we are running in a Docker container (standard way is checking for /.dockerenv)
# Alternatively, use host.docker.internal or localhost as a fallback if 'db' host is not reachable
# But a better practice for dev is to allow environment variable overrides.
default_uri = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", default_uri
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ── Models ──────────────────────────────────────────────────────────────────

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)


quest_categories = db.Table(
    "quest_categories",
    db.Column("quest_id", db.Integer, db.ForeignKey("quests.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
)


class Quest(db.Model):
    __tablename__ = "quests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    poster_name = db.Column(db.String(80), nullable=False, default="Anonymous")
    reward_gold = db.Column(db.Integer, nullable=False, default=0)
    danger_level = db.Column(
        db.String(20), nullable=False, default="Low"
    )  # Low, Medium, High, Legendary
    #TODO: use ENUM for danger_level
    status = db.Column(
        db.String(20), nullable=False, default="Open"
    )  # Open, Claimed, Completed
    #TODO: use ENUM for status
    claimed_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    categories = db.relationship(
        "Category", secondary=quest_categories, backref="quests", lazy="select"
    )

    def __repr__(self):
        return f"<Quest {self.title!r}>"


# ── CLI commands ────────────────────────────────────────────────────────────

SEED_CATEGORIES = [
    "Bounty", "Fetch", "Delivery", "Escort", "Investigation", "Gathering",
    "Political", "Arcane", "Charity", "Underworld", "Heroic",
]

@app.cli.command("seed-categories")
def seed_categories():
    """Seed the categories table. Safe to re-run (skips existing entries)."""
    inserted = 0
    for name in SEED_CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            inserted += 1
    db.session.commit()
    click.echo(f"Seeded {inserted} new categor{'y' if inserted == 1 else 'ies'} ({len(SEED_CATEGORIES) - inserted} already existed).")


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    status_filter = request.args.get("status", "all")
    category_filter = request.args.get("category", "")
    query = Quest.query.options(db.joinedload(Quest.categories)).order_by(Quest.created_at.desc())
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter(Quest.categories.any(Category.name == category_filter))
    quests = query.all()
    all_categories = Category.query.order_by(Category.name).all()
    return render_template(
        "index.html",
        quests=quests,
        current_filter=status_filter,
        current_category=category_filter,
        all_categories=all_categories,
    )


@app.route("/quest/new", methods=["GET", "POST"])
def create_quest():
    if request.method == "POST":
        quest = Quest(
            title=request.form["title"],
            description=request.form["description"],
            poster_name=request.form.get("poster_name") or "Anonymous",
            reward_gold=int(request.form.get("reward_gold", 0)),
            danger_level=request.form.get("danger_level", "Low"),
        )
        category_ids = request.form.getlist("categories")
        valid_ids = {str(c.id) for c in Category.query.all()}
        quest.categories = [
            db.session.get(Category, int(cid))
            for cid in category_ids
            if cid in valid_ids
        ]
        db.session.add(quest)
        db.session.commit()
        flash("Quest posted to the board!", "success")
        return redirect(url_for("index"))
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("quest_form.html", quest=None, all_categories=all_categories)


@app.route("/quest/<int:quest_id>")
def view_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    return render_template("quest_detail.html", quest=quest)


@app.route("/quest/<int:quest_id>/edit", methods=["GET", "POST"])
def edit_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    if request.method == "POST":
        quest.title = request.form["title"]
        quest.description = request.form["description"]
        quest.poster_name = request.form.get("poster_name") or quest.poster_name
        quest.reward_gold = int(request.form.get("reward_gold", 0))
        quest.danger_level = request.form.get("danger_level", quest.danger_level)
        category_ids = request.form.getlist("categories")
        valid_ids = {str(c.id) for c in Category.query.all()}
        quest.categories = [
            db.session.get(Category, int(cid))
            for cid in category_ids
            if cid in valid_ids
        ]
        db.session.commit()
        flash("Quest updated!", "success")
        return redirect(url_for("view_quest", quest_id=quest.id))
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("quest_form.html", quest=quest, all_categories=all_categories)


@app.route("/quest/<int:quest_id>/claim", methods=["POST"])
def claim_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    adventurer = request.form.get("adventurer_name", "A brave soul")
    quest.status = "Claimed"
    quest.claimed_by = adventurer
    db.session.commit()
    flash(f"{adventurer} claimed the quest!", "success")
    return redirect(url_for("view_quest", quest_id=quest.id))


@app.route("/quest/<int:quest_id>/complete", methods=["POST"])
def complete_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    quest.status = "Completed"
    db.session.commit()
    flash("Quest completed! Glory to the adventurer!", "success")
    return redirect(url_for("view_quest", quest_id=quest.id))


@app.route("/quest/<int:quest_id>/reopen", methods=["POST"])
def reopen_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    quest.status = "Open"
    quest.claimed_by = None
    db.session.commit()
    flash("Quest reopened on the board.", "success")
    return redirect(url_for("view_quest", quest_id=quest.id))


@app.route("/quest/<int:quest_id>/delete", methods=["POST"])
def delete_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    db.session.delete(quest)
    db.session.commit()
    flash("Quest torn from the board.", "success")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "ok"}, 200


# ── Init ────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
