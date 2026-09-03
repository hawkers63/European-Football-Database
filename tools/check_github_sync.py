#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_github_sync.py - GitHub Parity & Working Tree Audit Tool

Audits the local repository at C:\EuroDatabase against remote origin:
- Current branch and commit SHA
- Upstream tracking branch and ahead/behind counts
- Uncommitted, modified, and untracked files
- Remote connectivity and fetch status
- Build verification sanity check

Usage:
    python tools/check_github_sync.py
    python tools/check_github_sync.py --fetch
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run_git(args, cwd=ROOT):
    """Execute a git command and return (returncode, stdout, stderr)."""
    res = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return res.returncode, res.stdout, res.stderr


def audit_sync(do_fetch=False):
    print("=" * 68)
    print(" EUROPEAN FOOTBALL DATABASE - GITHUB SYNC & AUDIT")
    print("=" * 68)

    # 1. Remotes
    rc, remotes, _ = run_git(["remote", "-v"])
    if rc != 0 or not remotes:
        print(" [ERROR] No git remotes configured!")
        return 1

    origin_push = None
    for line in remotes.splitlines():
        if "(push)" in line:
            origin_push = line.split()[1]
            break
    print(f" Remote Target : {origin_push or remotes.splitlines()[0]}")

    # Optional fetch
    if do_fetch:
        print(" Fetching from origin...")
        frc, _, ferr = run_git(["fetch", "origin", "--prune"])
        if frc != 0:
            print(f" [WARN] Fetch encountered an issue: {ferr}")
        else:
            print(" Remote refs updated successfully.")

    # 2. Current branch & commit
    _, branch_raw, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    _, head_sha_raw, _ = run_git(["rev-parse", "--short", "HEAD"])
    _, head_msg_raw, _ = run_git(["log", "-1", "--format=%s", "HEAD"])
    branch = branch_raw.strip()
    head_sha = head_sha_raw.strip()
    head_msg = head_msg_raw.strip()
    print(f" Active Branch : {branch} ({head_sha})")
    print(f" Latest Commit : \"{head_msg}\"")

    # 3. Tracking branch & ahead/behind
    ahead = 0
    behind = 0
    _, tracking_raw, _ = run_git(["rev-parse", "--abbrev-ref", "@{u}"])
    tracking = tracking_raw.strip()
    has_upstream = bool(tracking and not tracking.startswith("@{u}"))

    if has_upstream:
        rc, counts, _ = run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"])
        if rc == 0 and counts:
            ahead, behind = map(int, counts.split())
            print(f" Tracking Ref  : {tracking}")
            if ahead == 0 and behind == 0:
                print(" Commit Status : [SYNCED] Local matches upstream perfectly.")
            else:
                badges = []
                status_parts = []
                if ahead > 0:
                    badges.append("[AHEAD]")
                    status_parts.append(f"{ahead} commit(s) AHEAD (unpushed)")
                if behind > 0:
                    badges.append("[BEHIND]")
                    status_parts.append(f"{behind} commit(s) BEHIND (unpulled)")
                print(f" Commit Status : {' '.join(badges)} {', '.join(status_parts)}")
        else:
            print(f" Tracking Ref  : {tracking} (could not calculate commit counts)")
    else:
        print(" Tracking Ref  : [NONE] Current branch has no upstream tracking ref set.")

    # 4. Working tree status
    _, status_raw, _ = run_git(["status", "--porcelain"])
    lines = [l for l in status_raw.splitlines() if l.strip()]

    staged = []
    unstaged = []
    untracked = []

    for l in lines:
        idx_status = l[0]
        work_status = l[1]
        filepath = l[3:]
        if idx_status in ("M", "A", "D", "R", "C"):
            staged.append(filepath)
        if work_status in ("M", "D"):
            unstaged.append(filepath)
        if idx_status == "?" and work_status == "?":
            untracked.append(filepath)

    print("\n Working Tree Health:")
    if not lines:
        print("  - Status     : [CLEAN] Working directory has no uncommitted changes.")
    else:
        print(f"  - Status     : [DIRTY] {len(lines)} file(s) require attention.")
        if staged:
            print(f"    * Staged for commit ({len(staged)}):")
            for f in staged[:5]:
                print(f"        + {f}")
            if len(staged) > 5:
                print(f"        ... and {len(staged)-5} more")
        if unstaged:
            print(f"    * Modified but unstaged ({len(unstaged)}):")
            for f in unstaged[:5]:
                print(f"        * {f}")
            if len(unstaged) > 5:
                print(f"        ... and {len(unstaged)-5} more")
        if untracked:
            print(f"    * Untracked ({len(untracked)}):")
            for f in untracked[:5]:
                print(f"        ? {f}")
            if len(untracked) > 5:
                print(f"        ... and {len(untracked)-5} more")

    # 5. Local branches overview
    print("\n Local Branches Overview:")
    _, branch_lines, _ = run_git(["branch", "-vv"])
    for bl in branch_lines.splitlines():
        marker = "-> " if bl.startswith("*") else "   "
        print(f"  {marker}{bl.lstrip('* ')}")

    # 6. Database build verification sanity check
    print("\n Verification Engine Sanity Check:")
    builder = os.path.join(ROOT, "build_database.py")
    if os.path.exists(builder):
        res = subprocess.run(
            [sys.executable, builder, "--force"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            print("  - build_database.py: [PASS] All aggregates verified cleanly.")
        else:
            print("  - build_database.py: [FAIL] Verification engine failed.")
            print(res.stderr or res.stdout)
    else:
        print("  - build_database.py: [WARN] File not found.")

    print("=" * 68)
    ok = not lines and has_upstream and ahead == 0 and behind == 0
    if not ok:
        hints = []
        if lines:
            hints.append("commit or clean the working tree")
        if ahead > 0:
            hints.append("git push")
        if behind > 0:
            hints.append("git pull --rebase")
        if not has_upstream:
            hints.append("git push -u origin HEAD")
        print(" Remediation   : " + "; ".join(hints) + ".")
    return 0 if ok else 1


if __name__ == "__main__":
    fetch_flag = "--fetch" in sys.argv
    sys.exit(audit_sync(do_fetch=fetch_flag))
