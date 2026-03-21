#!/usr/bin/env python3
"""
Issue Command Generator for Zenbid
Reads FEATURE_ROADMAP.md and generates gh CLI commands to create GitHub issues.

Usage:
    python scripts/generate-issue-commands.py

Output:
    PowerShell commands ready to copy/paste
"""

import re
from pathlib import Path

def parse_roadmap_section(content, section_header):
    """Extract items from a specific priority section of the roadmap."""
    # Find the section
    pattern = rf"## {re.escape(section_header)}.*?\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    section_content = match.group(1)
    
    # Parse table rows
    items = []
    lines = section_content.split('\n')
    
    for line in lines:
        # Look for table rows with | separators
        if '|' in line and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5 and parts[1]:  # Has feature name
                feature = parts[1].replace('**', '').strip()
                status = parts[2].strip()
                effort = parts[3] if len(parts) > 3 else 'Medium'
                notes = parts[-1].strip() if len(parts) > 4 else ''
                
                # Skip if already done
                if '✅' in status or 'Done' in status:
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
    """Determine appropriate labels based on item and section."""
    labels = []
    
    # Type label
    if 'bug' in item['name'].lower() or 'fix' in item['name'].lower():
        labels.append('bug')
    else:
        labels.append('enhancement')
    
    # Priority from section
    if 'CRITICAL' in section:
        labels.append('CRITICAL-priority')
    elif 'HIGH' in section:
        labels.append('HIGH-priority')
    elif 'MEDIUM' in section:
        labels.append('MEDIUM-priority')
    else:
        labels.append('FUTURE-priority')
    
    # Feature area labels (smart detection)
    name_lower = item['name'].lower()
    notes_lower = item['notes'].lower()
    combined = f"{name_lower} {notes_lower}"
    
    if 'agentx' in combined or 'ai panel' in combined or 'ai' in combined:
        labels.append('ai-integration')
    if 'assembly' in combined:
        labels.append('assembly-builder')
    if 'estimate' in combined or 'line item' in combined:
        labels.append('estimates')
    if 'wbs' in combined:
        labels.append('wbs')
    if 'auth' in combined or 'login' in combined or 'password' in combined or 'role' in combined:
        labels.append('auth')
    if 'multi-tenant' in combined or 'company' in combined or 'isolation' in combined:
        labels.append('multi-tenant')
    if 'proposal' in combined or 'report' in combined or 'pdf' in combined:
        labels.append('reporting')
    if 'deploy' in combined or 'digitalocean' in combined or 'server' in combined:
        labels.append('deployment')
    if 'security' in combined or 'csrf' in combined or 'xss' in combined:
        labels.append('security')
    if 'database' in combined or 'schema' in combined or 'migration' in combined:
        labels.append('database')
    
    return ','.join(labels)

def generate_issue_body(item):
    """Generate issue body text from roadmap item."""
    body_parts = []
    
    # Add notes as description if available
    if item['notes']:
        body_parts.append(f"## Description\n{item['notes']}")
    
    # Add priority
    section_priority = item['section'].split()[0]  # Extract CRITICAL, HIGH, etc.
    body_parts.append(f"\n## Priority\n{section_priority} - {item['section']}")
    
    # Add effort estimate
    if item['effort']:
        body_parts.append(f"\n## Effort Estimate\n{item['effort']}")
    
    # Add reference
    body_parts.append(f"\n## Reference\nFEATURE_ROADMAP.md - {item['section']}")
    
    # Add acceptance criteria placeholder
    body_parts.append("\n## Acceptance Criteria\n- [ ] Feature complete\n- [ ] Tested\n- [ ] Documented")
    
    return "\n".join(body_parts)

def generate_gh_command(item):
    """Generate gh issue create command."""
    title_prefix = "[BUG]" if 'bug' in determine_labels(item, item['section']) else "[FEATURE]"
    title = f"{title_prefix} {item['name']}"
    
    # Escape quotes in body
    body = generate_issue_body(item).replace('"', '\\"').replace('\n', '\\n\\n')
    
    labels = determine_labels(item, item['section'])
    
    # PowerShell-friendly format (no line breaks in command)
    cmd = f'gh issue create --title "{title}" --body "{body}" --label "{labels}"'
    
    return cmd

def main():
    """Main function to parse roadmap and generate commands."""
    
    # Read FEATURE_ROADMAP.md
    roadmap_path = Path(__file__).parent.parent / 'FEATURE_ROADMAP.md'
    
    if not roadmap_path.exists():
        print(f"❌ Error: FEATURE_ROADMAP.md not found at {roadmap_path}")
        return
    
    content = roadmap_path.read_text(encoding='utf-8')
    
    # Parse different priority sections
    sections = [
        '🔥 CRITICAL PRIORITY',
        '🎯 HIGH PRIORITY',
        '📊 MEDIUM PRIORITY',
        '🔮 FUTURE PRIORITY'
    ]
    
    all_items = []
    for section in sections:
        items = parse_roadmap_section(content, section)
        all_items.extend(items)
    
    if not all_items:
        print("✅ No open items found in FEATURE_ROADMAP.md")
        print("   All items are either complete or already tracked!")
        return
    
    # Generate commands
    print("# GitHub Issue Creation Commands")
    print("# Generated from FEATURE_ROADMAP.md")
    print("# Copy and paste these into PowerShell\n")
    
    for idx, item in enumerate(all_items, 1):
        print(f"# {idx}. {item['name']} ({item['section']})")
        print(generate_gh_command(item))
        print()
    
    print(f"\n# Total: {len(all_items)} issues to create")
    print("# Review each command before running!")

if __name__ == '__main__':
    main()
