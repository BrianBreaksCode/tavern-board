import enum
from datetime import datetime, timezone

from app.extensions import db


class DangerLevel(enum.Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Legendary = "Legendary"


class QuestStatus(enum.Enum):
    Open = "Open"
    Claimed = "Claimed"
    Completed = "Completed"


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
        db.Enum(DangerLevel), nullable=False, default=DangerLevel.Low
    )
    status = db.Column(
        db.Enum(QuestStatus), nullable=False, default=QuestStatus.Open
    )
    claimed_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    categories = db.relationship(
        "Category", secondary=quest_categories, backref="quests", lazy="select"
    )

    def __repr__(self):
        return f"<Quest {self.title!r}>"
