from datetime import datetime, timezone

from app.extensions import db


quest_categories = db.Table(
    "quest_categories",
    db.Column("quest_id", db.Integer, db.ForeignKey("quests.id"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)


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
