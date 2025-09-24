#!/usr/bin/env python3

import os
import subprocess
import sys
from datetime import datetime
import pytz
from typing import List, Optional, Tuple
from collections import defaultdict

def get_commit_log(repo_path: str) -> Optional[List[Tuple[str, datetime]]]:
    """
    Get the commit log with committer emails and dates from the given git repository path in PST.
    
    Args:
        repo_path (str): Path to the git repository
        
    Returns:
        Optional[List[Tuple[str, datetime]]]: List of (email, commit_date) tuples, or None if there was an error
    """
    
    # Validate repository path
    if not os.path.exists(repo_path):
        print(f"Error: Path '{repo_path}' does not exist.")
        return None
    
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: '{repo_path}' is not a valid Git repository.")
        return None

    try:
        # Run git log command to get both committer email and commit dates
        log_output = subprocess.check_output(
            ["git", "-C", repo_path, "log", "--pretty=format:%ce|%cd", "--date=iso-strict"],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Define timezone for conversion
        pst = pytz.timezone('America/Los_Angeles')
        
        # Parse and convert each entry
        parsed_commits = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
                
            try:
                # Split the line into email and date
                email, date_str = line.split('|', 1)
                
                # Parse the ISO format date with timezone
                utc_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                pst_time = utc_time.astimezone(pst)
                parsed_commits.append((email.strip(), pst_time))
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse line '{line}': {str(e)}")
        
        if not parsed_commits:
            print(f"Warning: No valid commits found in repository '{repo_path}'")
            return None
            
        # Sort by email first, then by date within each email group
        parsed_commits.sort(key=lambda x: (x[0], x[1]))
        
        # Group commits by email for display
        commits_by_email = defaultdict(list)
        for email, commit_date in parsed_commits:
            commits_by_email[email].append(commit_date)
        
        # Display the commit information grouped by email
        print(f"\nCommits grouped by committer email (PST) for repository at '{repo_path}':")
        print("=" * 80)
        
        total_commits = 0
        for email in sorted(commits_by_email.keys()):
            dates = commits_by_email[email]
            print(f"\n📧 {email} ({len(dates)} commits):")
            print("-" * 60)
            for pst_time in dates:
                print(f"  {pst_time.strftime('%A, %Y-%m-%d %I:%M:%S %p %Z')}")
            total_commits += len(dates)
        
        print("=" * 80)
        print(f"Total commits: {total_commits}")
        print(f"Total committers: {len(commits_by_email)}")
        
        return parsed_commits
    
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.output}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: python3 git_analytics.py <path_to_git_repo>")
        sys.exit(1)
        
    repo_path = sys.argv[1]
    get_commit_log(repo_path)

if __name__ == "__main__":
    main()