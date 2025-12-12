#!/usr/bin/env python3
"""
Database Migration Script
Adds team_home and team_away columns to games table
"""
import os
import sys
from app import create_app, db

def migrate():
    """Run database migration"""
    app = create_app()

    with app.app_context():
        try:
            # Check if columns already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('games')]

            if 'team_home' in columns and 'team_away' in columns:
                print("✓ Columns already exist. No migration needed.")
                return True

            # Add columns using raw SQL
            with db.engine.connect() as conn:
                if 'team_home' not in columns:
                    print("Adding team_home column...")
                    conn.execute(db.text("ALTER TABLE games ADD COLUMN team_home VARCHAR(50)"))
                    conn.commit()
                    print("✓ team_home column added")

                if 'team_away' not in columns:
                    print("Adding team_away column...")
                    conn.execute(db.text("ALTER TABLE games ADD COLUMN team_away VARCHAR(50)"))
                    conn.commit()
                    print("✓ team_away column added")

            print("\n✓ Migration completed successfully!")
            return True

        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}", file=sys.stderr)
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
