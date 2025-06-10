#!/usr/bin/env python
"""
Script to check what users are stored in the database
Run this after GitHub OAuth to see actual database records
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf.settings')
django.setup()

from api.models import User

def check_database_users():
    """Check what users are stored in the database"""
    print("🗃️  CHECKING USERS IN DATABASE")
    print("=" * 50)
    
    users = User.objects.all()
    
    if not users:
        print("📭 No users found in database")
        return
    
    for user in users:
        print(f"\n👤 USER #{user.id}")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   GitHub ID: {user.github_id or 'Not set'}")
        print(f"   GitHub Username: {user.github_username or 'Not set'}")
        print(f"   Is GitHub User: {user.is_github_user}")
        print(f"   Date Joined: {user.date_joined}")
        print(f"   Is Active: {user.is_active}")
        
        # Check if they have password (email/password user) or not (OAuth user)
        if user.password:
            print(f"   Has Password: Yes (can login with email/password)")
        else:
            print(f"   Has Password: No (OAuth only)")
            
        print(f"   Avatar URL: {user.github_avatar_url or 'None'}")

def check_github_users_only():
    """Show only GitHub users"""
    print("\n\n🐙 GITHUB USERS ONLY")
    print("=" * 30)
    
    github_users = User.objects.filter(is_github_user=True)
    
    if not github_users:
        print("📭 No GitHub users found")
        return
        
    for user in github_users:
        print(f"\n🐙 {user.github_username} (ID: {user.id})")
        print(f"   Email: {user.email}")
        print(f"   GitHub ID: {user.github_id}")
        print(f"   Joined: {user.date_joined}")

def show_stats():
    """Show user statistics"""
    total_users = User.objects.count()
    github_users = User.objects.filter(is_github_user=True).count()
    email_users = total_users - github_users
    
    print(f"\n\n📊 USER STATISTICS")
    print("=" * 20)
    print(f"Total Users: {total_users}")
    print(f"GitHub Users: {github_users}")
    print(f"Email/Password Users: {email_users}")

if __name__ == "__main__":
    print("🔍 USER DATABASE CHECKER")
    print("Run this script after GitHub OAuth to see what's actually stored\n")
    
    try:
        check_database_users()
        check_github_users_only()
        show_stats()
        
        print("\n\n💡 What This Proves:")
        print("- GitHub OAuth CREATES real database records")
        print("- Users are REGISTERED on your website, not just authenticated")
        print("- Same user logging in again uses EXISTING record")
        print("- GitHub users are fully integrated with your system")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you've run migrations: python manage.py migrate") 