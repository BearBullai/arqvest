#!/usr/bin/env python3
"""
Script to fix database schema issues by recreating the database with correct schema.
"""

import os
from app import app, db
from models import User, Security, PortfolioSnapshot, Transaction

def fix_database():
    """Recreate the database with correct schema"""
    
    with app.app_context():
        print("Fixing database schema...")
        
        # Drop all tables and recreate them
        db.drop_all()
        print("✓ Dropped all existing tables")
        
        # Create all tables with correct schema
        db.create_all()
        print("✓ Created all tables with correct schema")
        
        # Create a default user
        default_user = User(
            name="Default User",
            email="default@example.com",
            phone="0000000000"
        )
        default_user.set_password("changeme123")
        db.session.add(default_user)
        db.session.commit()
        print("✓ Created default user")
        
        print("\nDatabase fixed successfully!")
        print("Default user credentials:")
        print("Email: default@example.com")
        print("Password: changeme123")
        print("\nYou can now run the application.")

if __name__ == "__main__":
    fix_database() 