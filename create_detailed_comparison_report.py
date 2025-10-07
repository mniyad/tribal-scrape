#!/usr/bin/env python3
"""
Create detailed HTML comparison report with fuzzy matching
"""
import json
from datetime import datetime
from difflib import SequenceMatcher

def parse_gedcom(filename):
    """Parse GEDCOM file to extract individuals and families"""
    people = {}
    families = {}

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by records
    records = content.split('\n0 @')[1:]

    # Parse individuals
    for record in records:
        if not record.startswith('I'):
            continue

        lines = record.split('\n')
        person_id = lines[0].split('@')[0]

        person = {
            'id': person_id,
            'name': None,
            'birth': None,
            'death': None,
            'sex': None,
            'famc': None,  # Family as child
            'fams': []     # Families as spouse
        }

        for i, line in enumerate(lines):
            if ' NAME ' in line:
                name = line.split(' NAME ')[1].strip()
                person['name'] = name.replace('/', '').strip()
            elif ' SEX ' in line:
                person['sex'] = line.split(' SEX ')[1].strip()
            elif ' BIRT' in line:
                for j in range(i+1, min(i+5, len(lines))):
                    if ' DATE ' in lines[j]:
                        person['birth'] = lines[j].split(' DATE ')[1].strip()
                        break
            elif ' DEAT' in line:
                for j in range(i+1, min(i+5, len(lines))):
                    if ' DATE ' in lines[j]:
                        person['death'] = lines[j].split(' DATE ')[1].strip()
                        break
            elif ' FAMC @' in line:
                # Family as child
                fam_id = line.split('@')[1]
                person['famc'] = fam_id
            elif ' FAMS @' in line:
                # Family as spouse
                fam_id = line.split('@')[1]
                person['fams'].append(fam_id)

        if person['name']:
            people[person_id] = person

    # Parse families
    for record in records:
        if not record.startswith('F'):
            continue

        lines = record.split('\n')
        fam_id = lines[0].split('@')[0]

        family = {
            'id': fam_id,
            'husband': None,
            'wife': None,
            'children': []
        }

        for line in lines:
            if ' HUSB @' in line:
                family['husband'] = line.split('@')[1]
            elif ' WIFE @' in line:
                family['wife'] = line.split('@')[1]
            elif ' CHIL @' in line:
                child_id = line.split('@')[1]
                family['children'].append(child_id)

        families[fam_id] = family

    # Add parent and children information to people
    for person in people.values():
        person['father'] = None
        person['mother'] = None
        person['children'] = []

        # Add parents
        if person['famc'] and person['famc'] in families:
            fam = families[person['famc']]
            if fam['husband'] and fam['husband'] in people:
                person['father'] = people[fam['husband']]['name']
            if fam['wife'] and fam['wife'] in people:
                person['mother'] = people[fam['wife']]['name']

        # Add children
        for fam_id in person['fams']:
            if fam_id in families:
                for child_id in families[fam_id]['children']:
                    if child_id in people:
                        person['children'].append(people[child_id]['name'])

    return people

def extract_tribal_names(tribal_data):
    """Extract all unique names from the Tribal database with parent and children info"""
    names = set()
    pid_to_names = {}
    name_to_info = {}  # Store parent and children information for each name

    for pid, person in tribal_data['people'].items():
        # Get names from children connections
        for child in person.get('children', []):
            name = child.get('name', '').strip()
            if name and name != 'more..':
                names.add(name)
                child_pid = child.get('pid')
                if child_pid:
                    if child_pid not in pid_to_names:
                        pid_to_names[child_pid] = set()
                    pid_to_names[child_pid].add(name)

    # Build parent relationships and children from the data structure
    # In Tribal data, if someone appears in a person's children list, that person is the parent
    for pid, person in tribal_data['people'].items():
        parent_names = pid_to_names.get(int(pid), set())
        parent_name = list(parent_names)[0] if parent_names else None

        # Get this person's children
        person_children = []
        for child in person.get('children', []):
            child_name = child.get('name', '').strip()
            if child_name and child_name != 'more..':
                person_children.append(child_name)

                # Add parent relationship
                if child_name not in name_to_info:
                    name_to_info[child_name] = {'parents': [], 'children': []}
                if parent_name and parent_name not in name_to_info[child_name]['parents']:
                    name_to_info[child_name]['parents'].append(parent_name)

        # Store children for this parent
        if parent_name and person_children:
            if parent_name not in name_to_info:
                name_to_info[parent_name] = {'parents': [], 'children': []}
            name_to_info[parent_name]['children'].extend(person_children)

    return names, pid_to_names, name_to_info

def normalize_name(name):
    """Normalize name for comparison"""
    if not name:
        return ""
    name = name.lower().strip()

    # Handle "Lastname, Firstname" format
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            name = f"{parts[1].strip()} {parts[0].strip()}"

    name = name.replace('.', '')
    name = name.replace('(', '').replace(')', '')
    name = ' '.join(name.split())
    return name

def similarity_ratio(name1, name2):
    """Calculate similarity ratio between two names"""
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    return SequenceMatcher(None, norm1, norm2).ratio()

def find_fuzzy_matches(myheritage_people, tribal_names, threshold=0.75):
    """Find fuzzy matches between databases"""
    fuzzy_matches = []

    for mh_person in myheritage_people.values():
        mh_name = mh_person['name']
        best_match = None
        best_ratio = 0

        for tribal_name in tribal_names:
            ratio = similarity_ratio(mh_name, tribal_name)
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = tribal_name

        if best_match:
            fuzzy_matches.append({
                'myheritage_name': mh_name,
                'tribal_name': best_match,
                'similarity': round(best_ratio * 100, 1)
            })

    return fuzzy_matches

def get_family_context(person, person_info):
    """Get family context for display: parents if available, else adult children"""
    if person.get('father') or person.get('mother'):
        # Show parents
        parts = []
        if person.get('father'):
            parts.append(f"Father: {person['father']}")
        if person.get('mother'):
            parts.append(f"Mother: {person['mother']}")
        return ' | '.join(parts)
    elif person.get('children'):
        # Show children (limit to 3)
        children = person['children'][:3]
        children_str = ', '.join(children)
        if len(person['children']) > 3:
            children_str += f" (+{len(person['children']) - 3} more)"
        return f"Children: {children_str}"
    return "N/A"

def get_tribal_family_context(name, name_info):
    """Get family context for Tribal data: parents if available, else children"""
    info = name_info.get(name, {})
    parents = info.get('parents', [])
    children = info.get('children', [])

    if parents:
        return ', '.join(list(set(parents))[:2])  # Show up to 2 unique parents
    elif children:
        # Show children (limit to 3)
        unique_children = list(set(children))[:3]
        children_str = ', '.join(unique_children)
        if len(set(children)) > 3:
            children_str += f" (+{len(set(children)) - 3} more)"
        return f"Children: {children_str}"
    return "N/A"

def create_html_report():
    """Create detailed HTML comparison report"""
    print("Loading databases...")

    # Load Tribal database
    with open('SAIKURA_RESILIENT_FAMILY_DATABASE.json', 'r', encoding='utf-8') as f:
        tribal_data = json.load(f)

    # Parse MyHeritage GEDCOM
    myheritage_people = parse_gedcom('MyHeritage.ged')

    # Extract names from Tribal database
    tribal_names, pid_to_names, tribal_name_to_info = extract_tribal_names(tribal_data)

    print(f"MyHeritage: {len(myheritage_people)} people")
    print(f"Tribal: {len(tribal_names)} unique names")

    # Create normalized name mappings
    myheritage_normalized = {normalize_name(p['name']): p for p in myheritage_people.values() if p['name']}
    tribal_normalized = {normalize_name(name): name for name in tribal_names}

    # Find exact matches
    exact_matches = []
    only_in_myheritage = []
    only_in_tribal = []

    for norm_name, person in myheritage_normalized.items():
        if norm_name in tribal_normalized:
            exact_matches.append({
                'myheritage_name': person['name'],
                'tribal_name': tribal_normalized[norm_name],
                'birth': person.get('birth'),
                'death': person.get('death')
            })
        else:
            only_in_myheritage.append(person)

    for norm_name, original_name in tribal_normalized.items():
        if norm_name not in myheritage_normalized:
            only_in_tribal.append(original_name)

    # Find fuzzy matches
    print("Finding fuzzy matches...")
    unmatched_myheritage = [p for p in myheritage_people.values()
                           if normalize_name(p['name']) not in tribal_normalized]
    unmatched_tribal = [name for name in tribal_names
                          if normalize_name(name) not in myheritage_normalized]

    fuzzy_matches = find_fuzzy_matches(
        {p['id']: p for p in unmatched_myheritage},
        unmatched_tribal,
        threshold=0.70
    )

    # Create sets of fuzzy matched names for exclusion
    fuzzy_matched_mh = {match['myheritage_name'] for match in fuzzy_matches}
    fuzzy_matched_tribal = {match['tribal_name'] for match in fuzzy_matches}

    # Update "only in" lists to exclude fuzzy matches
    only_in_myheritage = [p for p in only_in_myheritage if p['name'] not in fuzzy_matched_mh]
    only_in_tribal = [name for name in only_in_tribal if name not in fuzzy_matched_tribal]

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tribal vs MyHeritage Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
        }}
        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            color: white;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            margin-top: 0;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.95;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .match-exact {{
            background-color: #d4edda;
        }}
        .match-fuzzy {{
            background-color: #fff3cd;
        }}
        .no-match {{
            background-color: #f8d7da;
        }}
        .similarity {{
            font-weight: bold;
            color: #e67e22;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .filter-box {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        input[type="text"] {{
            width: 100%;
            padding: 10px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 14px;
        }}
        input[type="text"]:focus {{
            outline: none;
            border-color: #3498db;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-success {{
            background-color: #28a745;
            color: white;
        }}
        .badge-warning {{
            background-color: #ffc107;
            color: #000;
        }}
        .badge-danger {{
            background-color: #dc3545;
            color: white;
        }}
    </style>
</head>
<body>
    <h1>🔍 Tribal vs MyHeritage GEDCOM - Detailed Comparison</h1>

    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <span class="stat-number">{len(myheritage_people)}</span>
                <span class="stat-label">MyHeritage People</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(tribal_data['people'])}</span>
                <span class="stat-label">Tribal PIDs</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(tribal_names)}</span>
                <span class="stat-label">Tribal Unique Names</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(exact_matches)}</span>
                <span class="stat-label">Exact Matches</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(fuzzy_matches)}</span>
                <span class="stat-label">Fuzzy Matches (≥70%)</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(only_in_myheritage)}</span>
                <span class="stat-label">Only in MyHeritage</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{len(only_in_tribal)}</span>
                <span class="stat-label">Only in Tribal</span>
            </div>
            <div class="stat-box">
                <span class="stat-number">{round((len(exact_matches) / len(myheritage_people) * 100), 1)}%</span>
                <span class="stat-label">Exact Match Rate</span>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>✅ Exact Matches ({len(exact_matches)})</h2>
        <div class="filter-box">
            <input type="text" id="exactFilter" onkeyup="filterTable('exactTable', 'exactFilter')"
                   placeholder="Search exact matches...">
        </div>
        <table id="exactTable">
            <thead>
                <tr>
                    <th>#</th>
                    <th>MyHeritage Name</th>
                    <th>Tribal Name</th>
                    <th>Birth</th>
                    <th>Death</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

    for i, match in enumerate(sorted(exact_matches, key=lambda x: x['myheritage_name']), 1):
        html += f"""
                <tr class="match-exact">
                    <td>{i}</td>
                    <td>{match['myheritage_name']}</td>
                    <td>{match['tribal_name']}</td>
                    <td>{match.get('birth') or 'N/A'}</td>
                    <td>{match.get('death') or 'N/A'}</td>
                    <td><span class="badge badge-success">EXACT</span></td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>⚠️ Fuzzy/Approximate Matches ({len(fuzzy_matches)})</h2>
        <p>These are potential matches with similarity ≥70%. Please review manually.</p>
        <div class="filter-box">
            <input type="text" id="fuzzyFilter" onkeyup="filterTable('fuzzyTable', 'fuzzyFilter')"
                   placeholder="Search fuzzy matches...">
        </div>
        <table id="fuzzyTable">
            <thead>
                <tr>
                    <th>#</th>
                    <th>MyHeritage Name</th>
                    <th>Tribal Name</th>
                    <th>Similarity %</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

    for i, match in enumerate(sorted(fuzzy_matches, key=lambda x: -x['similarity']), 1):
        html += f"""
                <tr class="match-fuzzy">
                    <td>{i}</td>
                    <td>{match['myheritage_name']}</td>
                    <td>{match['tribal_name']}</td>
                    <td><span class="similarity">{match['similarity']}%</span></td>
                    <td><span class="badge badge-warning">FUZZY</span></td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>❌ Only in MyHeritage ({len(only_in_myheritage)})</h2>
        <p>People found in MyHeritage GEDCOM but not in Tribal extraction. Shows parents if available, otherwise adult children.</p>
        <div class="filter-box">
            <input type="text" id="mhOnlyFilter" onkeyup="filterTable('mhOnlyTable', 'mhOnlyFilter')"
                   placeholder="Search MyHeritage only...">
        </div>
        <table id="mhOnlyTable">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Family Context</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

    for i, person in enumerate(sorted(only_in_myheritage, key=lambda x: x['name']), 1):
        family_context = get_family_context(person, None)
        html += f"""
                <tr class="no-match">
                    <td>{i}</td>
                    <td>{person['name']}</td>
                    <td>{family_context}</td>
                    <td><span class="badge badge-danger">MISSING</span></td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>➕ Only in Tribal Extraction ({len(only_in_tribal)})</h2>
        <p>Names found in Tribal extraction but not in MyHeritage GEDCOM. Shows parents if available, otherwise children.</p>
        <div class="filter-box">
            <input type="text" id="tribalOnlyFilter" onkeyup="filterTable('tribalOnlyTable', 'tribalOnlyFilter')"
                   placeholder="Search Tribal only...">
        </div>
        <table id="tribalOnlyTable">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Name</th>
                    <th>Family Context</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""

    for i, name in enumerate(sorted(only_in_tribal), 1):
        family_context = get_tribal_family_context(name, tribal_name_to_info)
        html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{name}</td>
                    <td>{family_context}</td>
                    <td><span class="badge badge-danger">EXTRA</span></td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>

    <script>
        function filterTable(tableId, filterId) {
            const input = document.getElementById(filterId);
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');

            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }
        }
    </script>

    <div style="margin-top: 40px; padding: 20px; background: #ecf0f1; border-radius: 8px; text-align: center;">
        <p><strong>Report Generated:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>Tribal Extraction Tool - Saikura Family Tree Analysis</p>
    </div>
</body>
</html>
"""

    # Save HTML report
    output_file = 'TRIBAL_MYHERITAGE_DETAILED_REPORT.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n{'='*60}")
    print(f"HTML report saved: {output_file}")
    print(f"{'='*60}")
    print(f"Exact matches: {len(exact_matches)}")
    print(f"Fuzzy matches: {len(fuzzy_matches)}")
    print(f"Total potential matches: {len(exact_matches) + len(fuzzy_matches)}")
    print(f"Coverage: {round((len(exact_matches) + len(fuzzy_matches)) / len(myheritage_people) * 100, 1)}%")

if __name__ == "__main__":
    create_html_report()
