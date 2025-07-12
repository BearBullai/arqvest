#!/usr/bin/env python3
"""
Database migration script to add user_id columns to Security and PortfolioSnapshot tables.
This script handles the transition from a single-user system to a multi-user system.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text
from app import app, db
from models import User, Security, PortfolioSnapshot

def migrate_database():
    """Migrate the database to support multi-user functionality"""
    
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Check if user_id columns already exist
            inspector = db.inspect(db.engine)
            security_columns = [col['name'] for col in inspector.get_columns('security')]
            snapshot_columns = [col['name'] for col in inspector.get_columns('portfolio_snapshot')]
            
            print(f"Security table columns: {security_columns}")
            print(f"PortfolioSnapshot table columns: {snapshot_columns}")
            
            # Add user_id column to Security table if it doesn't exist
            if 'user_id' not in security_columns:
                print("Adding user_id column to Security table...")
                try:
                    # For SQLite, we need to recreate the table
                    if 'sqlite' in str(db.engine.url):
                        print("SQLite detected - recreating Security table...")
                        # Create new table with user_id
                        db.engine.execute(text("""
                            CREATE TABLE security_new (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER,
                                ticker VARCHAR(10) NOT NULL,
                                name VARCHAR(100) NOT NULL,
                                asset_class VARCHAR(50) NOT NULL,
                                purchase_price FLOAT NOT NULL,
                                current_price FLOAT NOT NULL,
                                quantity FLOAT NOT NULL,
                                purchase_date DATE NOT NULL,
                                sector VARCHAR(50),
                                country VARCHAR(50),
                                currency VARCHAR(3),
                                notes TEXT,
                                created_at DATETIME,
                                updated_at DATETIME
                            )
                        """))
                        
                        # Copy data from old table to new table
                        db.engine.execute(text("""
                            INSERT INTO security_new (
                                id, ticker, name, asset_class, purchase_price, current_price,
                                quantity, purchase_date, sector, country, currency, notes,
                                created_at, updated_at
                            ) SELECT 
                                id, ticker, name, asset_class, purchase_price, current_price,
                                quantity, purchase_date, sector, country, currency, notes,
                                created_at, updated_at
                            FROM security
                        """))
                        
                        # Drop old table and rename new table
                        db.engine.execute(text("DROP TABLE security"))
                        db.engine.execute(text("ALTER TABLE security_new RENAME TO security"))
                        
                    else:
                        db.engine.execute(text("ALTER TABLE security ADD COLUMN user_id INTEGER"))
                    
                    print("✓ Added user_id column to Security table")
                except Exception as e:
                    print(f"Error adding user_id to Security table: {e}")
                    return False
            
            # Add user_id column to PortfolioSnapshot table if it doesn't exist
            if 'user_id' not in snapshot_columns:
                print("Adding user_id column to PortfolioSnapshot table...")
                try:
                    # For SQLite, we need to recreate the table
                    if 'sqlite' in str(db.engine.url):
                        print("SQLite detected - recreating PortfolioSnapshot table...")
                        # Create new table with user_id
                        db.engine.execute(text("""
                            CREATE TABLE portfolio_snapshot_new (
                                id INTEGER PRIMARY KEY,
                                user_id INTEGER,
                                date DATE NOT NULL,
                                total_value FLOAT NOT NULL,
                                cash_value FLOAT,
                                created_at DATETIME
                            )
                        """))
                        
                        # Copy data from old table to new table
                        db.engine.execute(text("""
                            INSERT INTO portfolio_snapshot_new (
                                id, date, total_value, cash_value, created_at
                            ) SELECT 
                                id, date, total_value, cash_value, created_at
                            FROM portfolio_snapshot
                        """))
                        
                        # Drop old table and rename new table
                        db.engine.execute(text("DROP TABLE portfolio_snapshot"))
                        db.engine.execute(text("ALTER TABLE portfolio_snapshot_new RENAME TO portfolio_snapshot"))
                        
                    else:
                        db.engine.execute(text("ALTER TABLE portfolio_snapshot ADD COLUMN user_id INTEGER"))
                    
                    print("✓ Added user_id column to PortfolioSnapshot table")
                except Exception as e:
                    print(f"Error adding user_id to PortfolioSnapshot table: {e}")
                    return False
            
            # Create a default user if no users exist
            default_user = User.query.first()
            if not default_user:
                print("Creating default user for existing data...")
                try:
                    default_user = User(
                        name="Default User",
                        email="default@example.com",
                        phone="0000000000"
                    )
                    default_user.set_password("changeme123")
                    db.session.add(default_user)
                    db.session.commit()
                    print("✓ Created default user")
                except Exception as e:
                    print(f"Error creating default user: {e}")
                    return False
            
            # Update existing securities to belong to the default user
            existing_securities = Security.query.filter_by(user_id=None).all()
            if existing_securities:
                print(f"Updating {len(existing_securities)} existing securities...")
                try:
                    for security in existing_securities:
                        security.user_id = default_user.id
                    db.session.commit()
                    print("✓ Updated existing securities")
                except Exception as e:
                    print(f"Error updating securities: {e}")
                    return False
            
            # Update existing portfolio snapshots to belong to the default user
            existing_snapshots = PortfolioSnapshot.query.filter_by(user_id=None).all()
            if existing_snapshots:
                print(f"Updating {len(existing_snapshots)} existing portfolio snapshots...")
                try:
                    for snapshot in existing_snapshots:
                        snapshot.user_id = default_user.id
                    db.session.commit()
                    print("✓ Updated existing portfolio snapshots")
                except Exception as e:
                    print(f"Error updating portfolio snapshots: {e}")
                    return False
            
            print("✓ Database migration completed successfully!")
            print("\nImportant notes:")
            print("1. A default user has been created with email: default@example.com")
            print("2. Password for default user: changeme123")
            print("3. All existing securities and snapshots have been assigned to this user")
            print("4. Please change the default user's password or create new users")
            
            return True
            
        except Exception as e:
            print(f"Migration failed with error: {e}")
            return False

if __name__ == "__main__":
    success = migrate_database()
    if not success:
        print("Migration failed!")
        sys.exit(1)
    else:
        print("Migration completed successfully!") 