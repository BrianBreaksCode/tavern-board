import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://tavern:tavern@db:5432/tavern_board"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ── Models ──────────────────────────────────────────────────────────────────

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
    status = db.Column(
        db.String(20), nullable=False, default="Open"
    )  # Open, Claimed, Completed
    claimed_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Quest {self.title!r}>"


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    status_filter = request.args.get("status", "all")
    query = Quest.query.order_by(Quest.created_at.desc())
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    quests = query.all()
    return render_template("index.html", quests=quests, current_filter=status_filter)


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
        db.session.add(quest)
        db.session.commit()
        flash("Quest posted to the board!", "success")
        return redirect(url_for("index"))
    return render_template("quest_form.html", quest=None)


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
        db.session.commit()
        flash("Quest updated!", "success")
        return redirect(url_for("view_quest", quest_id=quest.id))
    return render_template("quest_form.html", quest=quest)


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
