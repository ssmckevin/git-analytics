#!/usr/bin/env python3

import os
import subprocess
import sys
from datetime import datetime
import pytz
from typing import List, Optional, Tuple
from collections import defaultdict

def get_commit_log(repo_path: str) -> Optional[List[Tuple[str, datetime, str]]]:
    """
    Get the commit log with committer emails, dates, and titles from the given git repository path in PST.
    
    Args:
        repo_path (str): Path to the git repository
        
    Returns:
        Optional[List[Tuple[str, datetime, str]]]: List of (email, commit_date, title) tuples
    """
    
    # Validate repository path
    if not os.path.exists(repo_path):
        print(f"Error: Path '{repo_path}' does not exist.")
        return None
    
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: '{repo_path}' is not a valid Git repository.")
        return None

    try:
        # Include commit title in the log
        log_output = subprocess.check_output(
            ["git", "-C", repo_path, "log", "--pretty=format:%ce|%cd|%s", "--date=iso-strict"],
            stderr=subprocess.STDOUT,
            text=True,         # Python 3.7+ preferred over universal_newlines
            encoding='utf-8'   # explicitly specify UTF-8 decoding
        )

        
        pst = pytz.timezone('America/Los_Angeles')
        
        parsed_commits = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
            try:
                email, date_str, title = line.split('|', 2)
                utc_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                pst_time = utc_time.astimezone(pst)
                parsed_commits.append((email.strip(), pst_time, title.strip()))
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse line '{line}': {str(e)}")
        
        if not parsed_commits:
            print(f"Warning: No valid commits found in repository '{repo_path}'")
            return None

        # Sort by email then date
        parsed_commits.sort(key=lambda x: (x[0], x[1]))

        # Group commits by email
        commits_by_email = defaultdict(list)
        for email, commit_date, title in parsed_commits:
            commits_by_email[email].append((commit_date, title))

        # Count commits per day
        commits_per_day = defaultdict(int)
        for _, commit_date, _ in parsed_commits:
            day = commit_date.strftime('%Y-%m-%d')
            commits_per_day[day] += 1

        # Display commits grouped by email
        print(f"\nCommits grouped by committer email (PST) for repository at '{repo_path}':")
        print("=" * 80)
        
        total_commits = 0
        for email in sorted(commits_by_email.keys()):
            commits = commits_by_email[email]
            print(f"\n📧 {email} ({len(commits)} commits):")
            print("-" * 60)
            for pst_time, title in commits:
                print(f"  {pst_time.strftime('%A, %Y-%m-%d %I:%M:%S %p %Z')} — {title}")
            total_commits += len(commits)

        print("=" * 80)
        print(f"Total commits: {total_commits}")
        print(f"Total committers: {len(commits_by_email)}")

        print("\nCommits per day:")
        for day in sorted(commits_per_day.keys()):
            print(f"  {day}: {commits_per_day[day]} commits")

        # === Average calculations ===
        num_days = len(commits_per_day)
        total_commits = sum(commits_per_day.values())

        # Count weekdays only (Mon–Fri)
        weekday_days = [
            date for date in commits_per_day.keys()
            if datetime.strptime(date, "%Y-%m-%d").weekday() < 5
        ]
        num_weekdays = len(weekday_days)

        avg_per_day = total_commits / num_days if num_days else 0
        avg_per_weekday = total_commits / num_weekdays if num_weekdays else 0

        print(f"Commit Averages:")
        print(f"  Average commits per day: {avg_per_day:.2f}")
        print(f"  Average commits per weekday (no weekends): {avg_per_weekday:.2f}")

        
        return parsed_commits

    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.output}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 git_analytics.py <path_to_git_repo>")
        sys.exit(1)
        
    repo_path = sys.argv[1]
    get_commit_log(repo_path)

if __name__ == "__main__":
    main()

