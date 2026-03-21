#!/usr/bin/env python3
"""
Automated Issue Creator for Zenbid
Reads FEATURE_ROADMAP.md and automatically creates GitHub issues.

Usage:
    python scripts/auto-create-issues.py [--dry-run] [--priority CRITICAL|HIGH|MEDIUM|FUTURE]

Examples:
    python scripts/auto-create-issues.py --dry-run              # Preview what would be created
    python scripts/auto-create-issues.py --priority CRITICAL    # Only create CRITICAL issues
    python scripts/auto-create-issues.py                        # Create all open issues

Requirements:
    - gh CLI installed and authenticated
    - Run from project root directory
"""

import subprocess
import sys
import re
import argparse
from pathlib import Path

def run_gh_command(args, dry_run=False):
    """Execute gh CLI command."""
    if dry_run:
        print(f"[DRY RUN] Would run: gh {' '.join(args)}")
        return True, "dry-run-success"
    
    try:
        result = subprocess.run(
            ['gh'] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, "gh CLI not found - install from https://cli.github.com"

def parse_roadmap_section(content, section_header):
    """Extract items from a specific priority section."""
    pattern = rf"## {re.escape(section_header)}.*?\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    section_content = match.group(1)
    items = []
    lines = section_content.split('\n')
    
    for line in lines:
        if '|' in line and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5 and parts[1]:
                feature = parts[1].replace('**', '').strip()
                status = parts[2].strip()
                effort = parts[3] if len(parts) > 3 else 'Medium'
                notes = parts[-1].strip() if len(parts) > 4 else ''
                
                if '✅' in status or 'Done' in status or '❌' in status:
                    continue
                    
                items.append({
                    'name': feature,
                    'status': status,
                    'effort': effort,
                    'notes': notes,
                    'section': section_header
                })
    
    return items

def determine_labels(item, section):
    """Determine labels based on item content."""
    labels = []
    
    # Type
    if 'bug' in item['name'].lower() or 'fix' in item['name'].lower():
        labels.append('bug')
    else:
        labels.append('enhancement')
    
    # Priority
    if 'CRITICAL' in section:
        labels.append('CRITICAL-priority')
    elif 'HIGH' in section:
        labels.append('HIGH-priority')
    elif 'MEDIUM' in section:
        labels.append('MEDIUM-priority')
    else:
        labels.append('FUTURE-priority')
    
    # Feature areas (smart detection)
    combined = f"{item['name'].lower()} {item['notes'].lower()}"
    
    area_map = {
        'ai-integration': ['agentx', 'ai panel', 'ai', 'claude'],
        'assembly-builder': ['assembly'],
        'estimates': ['estimate', 'line item'],
        'wbs': ['wbs', 'work breakdown'],
        'auth': ['auth', 'login', 'password', 'role', 'viewer'],
        'multi-tenant': ['multi-tenant', 'company', 'isolation'],
        'reporting': ['proposal', 'report', 'pdf', 'export'],
        'deployment': ['deploy', 'digitalocean', 'server', 'nginx'],
        'security': ['security', 'csrf', 'xss', 'sql injection'],
        'database': ['database', 'schema', 'migration']
    }
    
    for label, keywords in area_map.items():
        if any(keyword in combined for keyword in keywords):
            labels.append(label)
    
    return labels

def create_issue(item, dry_run=False):
    """Create a GitHub issue for the roadmap item."""
    # Determine title prefix
    is_bug = 'bug' in item['name'].lower() or 'fix' in item['name'].lower()
    prefix = "[BUG]" if is_bug else "[FEATURE]"
    title = f"{prefix} {item['name']}"
    
    # Build body
    body_parts = []
    
    if item['notes']:
        body_parts.append(f"## Description\n{item['notes']}")
    
    section_priority = item['section'].split()[0]
    body_parts.append(f"\n## Priority\n{section_priority} - {item['section']}")
    
    if item['effort']:
        body_parts.append(f"\n## Effort Estimate\n{item['effort']}")
    
    body_parts.append(f"\n## Reference\nFEATURE_ROADMAP.md - {item['section']}")
    body_parts.append("\n## Acceptance Criteria\n- [ ] Feature complete\n- [ ] Tested\n- [ ] Documented in Agent_MD.md if needed")
    
    body = "\n".join(body_parts)
    
    # Get labels
    labels = determine_labels(item, item['section'])
    label_str = ",".join(labels)
    
    # Create issue via gh CLI
    args = [
        'issue', 'create',
        '--title', title,
        '--body', body,
        '--label', label_str
    ]
    
    success, output = run_gh_command(args, dry_run)
    
    return success, output, title

def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description='Auto-create GitHub issues from FEATURE_ROADMAP.md')
    parser.add_argument('--dry-run', action='store_true', help='Preview without creating issues')
    parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'FUTURE'], 
                       help='Only create issues for specific priority level')
    args = parser.parse_args()
    
    # Read roadmap
    roadmap_path = Path('FEATURE_ROADMAP.md')
    
    if not roadmap_path.exists():
        print("❌ Error: FEATURE_ROADMAP.md not found in current directory")
        print("   Run this script from project root: python scripts/auto-create-issues.py")
        sys.exit(1)
    
    content = roadmap_path.read_text(encoding='utf-8')
    
    # Parse sections
    section_map = {
        'CRITICAL': '🔥 CRITICAL PRIORITY',
        'HIGH': '🎯 HIGH PRIORITY',
        'MEDIUM': '📊 MEDIUM PRIORITY',
        'FUTURE': '🔮 FUTURE PRIORITY'
    }
    
    sections_to_process = [section_map[args.priority]] if args.priority else list(section_map.values())
    
    all_items = []
    for section in sections_to_process:
        items = parse_roadmap_section(content, section)
        all_items.extend(items)
    
    if not all_items:
        print("✅ No open items found in FEATURE_ROADMAP.md")
        print("   All items are either complete or already tracked!")
        return
    
    # Header
    mode = "DRY RUN" if args.dry_run else "CREATING ISSUES"
    print(f"\n{'='*60}")
    print(f"  {mode}: {len(all_items)} issues from FEATURE_ROADMAP.md")
    print(f"{'='*60}\n")
    
    # Create issues
    created = []
    failed = []
    
    for idx, item in enumerate(all_items, 1):
        print(f"[{idx}/{len(all_items)}] {item['name']}...")
        
        success, output, title = create_issue(item, args.dry_run)
        
        if success:
            created.append(title)
            if not args.dry_run:
                print(f"  ✅ Created: {output.strip()}")
            else:
                print(f"  ✅ Would create")
        else:
            failed.append((title, output))
            print(f"  ❌ Failed: {output}")
        
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully created: {len(created)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\nFailed issues:")
        for title, error in failed:
            print(f"  - {title}")
            print(f"    Error: {error}")
    
    if not args.dry_run and created:
        print(f"\n🎉 Created {len(created)} new issues!")
        print("\nView them at: https://github.com/agentxt9-hub/Esimator-Agent/issues")
        print("\nNext: Add them to your project board manually or run:")
        print("  gh project item-add <project-number> --url <issue-url>")

if __name__ == '__main__':
    main()
