from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Category, Quest


quests_bp = Blueprint("quests", __name__)


@quests_bp.route("/")
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


@quests_bp.route("/quest/new", methods=["GET", "POST"])
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
        return redirect(url_for("quests.index"))
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("quest_form.html", quest=None, all_categories=all_categories)


@quests_bp.route("/quest/<int:quest_id>")
def view_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    return render_template("quest_detail.html", quest=quest)


@quests_bp.route("/quest/<int:quest_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("quests.view_quest", quest_id=quest.id))
    all_categories = Category.query.order_by(Category.name).all()
    return render_template("quest_form.html", quest=quest, all_categories=all_categories)


@quests_bp.route("/quest/<int:quest_id>/claim", methods=["POST"])
def claim_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    adventurer = request.form.get("adventurer_name", "A brave soul")
    quest.status = "Claimed"
    quest.claimed_by = adventurer
    db.session.commit()
    flash(f"{adventurer} claimed the quest!", "success")
    return redirect(url_for("quests.view_quest", quest_id=quest.id))


@quests_bp.route("/quest/<int:quest_id>/complete", methods=["POST"])
def complete_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    quest.status = "Completed"
    db.session.commit()
    flash("Quest completed! Glory to the adventurer!", "success")
    return redirect(url_for("quests.view_quest", quest_id=quest.id))


@quests_bp.route("/quest/<int:quest_id>/reopen", methods=["POST"])
def reopen_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    quest.status = "Open"
    quest.claimed_by = None
    db.session.commit()
    flash("Quest reopened on the board.", "success")
    return redirect(url_for("quests.view_quest", quest_id=quest.id))


@quests_bp.route("/quest/<int:quest_id>/delete", methods=["POST"])
def delete_quest(quest_id):
    quest = Quest.query.get_or_404(quest_id)
    db.session.delete(quest)
    db.session.commit()
    flash("Quest torn from the board.", "success")
    return redirect(url_for("quests.index"))


@quests_bp.route("/health")
def health():
    return {"status": "ok"}, 200
