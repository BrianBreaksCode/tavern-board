import click

from app.extensions import db
from app.models import Category


SEED_CATEGORIES = [
    "Bounty", "Fetch", "Delivery", "Escort", "Investigation", "Gathering",
    "Political", "Arcane", "Charity", "Underworld", "Heroic",
]


@click.command("seed-categories")
def seed_categories():
    """Seed the categories table. Safe to re-run (skips existing entries)."""
    inserted = 0
    for name in SEED_CATEGORIES:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            inserted += 1
    db.session.commit()
    click.echo(f"Seeded {inserted} new categor{'y' if inserted == 1 else 'ies'} ({len(SEED_CATEGORIES) - inserted} already existed).")
