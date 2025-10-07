#!/usr/bin/env python3
"""
Compare the Resilient Extraction with MyHeritage GEDCOM
"""
import json
from datetime import datetime

def parse_gedcom(filename):
    """Parse GEDCOM file to extract individuals"""
    people = {}

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by individual records
    individuals = content.split('\n0 @')[1:]  # Skip header

    for ind in individuals:
        if not ind.startswith('I'):
            continue

        lines = ind.split('\n')
        person_id = lines[0].split('@')[0]

        person = {
            'id': person_id,
            'name': None,
            'birth': None,
            'death': None,
            'sex': None
        }

        for i, line in enumerate(lines):
            if ' NAME ' in line:
                name = line.split(' NAME ')[1].strip()
                person['name'] = name.replace('/', '').strip()
            elif ' SEX ' in line:
                person['sex'] = line.split(' SEX ')[1].strip()
            elif ' BIRT' in line:
                # Look for date in next lines
                for j in range(i+1, min(i+5, len(lines))):
                    if ' DATE ' in lines[j]:
                        person['birth'] = lines[j].split(' DATE ')[1].strip()
                        break
            elif ' DEAT' in line:
                # Look for date in next lines
                for j in range(i+1, min(i+5, len(lines))):
                    if ' DATE ' in lines[j]:
                        person['death'] = lines[j].split(' DATE ')[1].strip()
                        break

        if person['name']:
            people[person_id] = person

    return people

def extract_resilient_names(resilient_data):
    """Extract all unique names from the resilient database"""
    names = set()
    pid_to_names = {}

    for pid, person in resilient_data['people'].items():
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

    return names, pid_to_names

def normalize_name(name):
    """Normalize name for comparison"""
    if not name:
        return ""
    # Remove common suffixes and normalize
    name = name.lower().strip()

    # Handle "Lastname, Firstname" format - convert to "firstname lastname"
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            # Reverse: "Yoosuf, Ahmed" -> "ahmed yoosuf"
            name = f"{parts[1].strip()} {parts[0].strip()}"

    name = name.replace('.', '')
    name = name.replace('(', '').replace(')', '')
    name = ' '.join(name.split())
    return name

def compare_databases():
    """Compare Resilient extraction with MyHeritage GEDCOM"""
    print("Loading databases...")

    # Load resilient database
    with open('SAIKURA_RESILIENT_FAMILY_DATABASE.json', 'r', encoding='utf-8') as f:
        resilient_data = json.load(f)

    # Parse MyHeritage GEDCOM
    myheritage_people = parse_gedcom('MyHeritage.ged')

    # Extract names from resilient database
    resilient_names, pid_to_names = extract_resilient_names(resilient_data)

    print(f"\nMyHeritage GEDCOM: {len(myheritage_people)} people")
    print(f"Resilient Database: {len(resilient_data['people'])} PIDs")
    print(f"Unique names in Resilient: {len(resilient_names)}")

    # Create normalized name mappings
    myheritage_normalized = {normalize_name(p['name']): p for p in myheritage_people.values() if p['name']}
    resilient_normalized = {normalize_name(name): name for name in resilient_names}

    # Find matches and gaps
    in_both = set()
    only_in_myheritage = set()
    only_in_resilient = set()

    for norm_name, person in myheritage_normalized.items():
        if norm_name in resilient_normalized:
            in_both.add(person['name'])
        else:
            only_in_myheritage.add(person['name'])

    for norm_name, original_name in resilient_normalized.items():
        if norm_name not in myheritage_normalized:
            only_in_resilient.add(original_name)

    # Create comparison report
    report = {
        "comparison_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "myheritage_total": len(myheritage_people),
            "resilient_total_pids": len(resilient_data['people']),
            "resilient_unique_names": len(resilient_names),
            "people_in_both": len(in_both),
            "only_in_myheritage": len(only_in_myheritage),
            "only_in_resilient": len(only_in_resilient),
            "match_percentage": round(len(in_both) / len(myheritage_people) * 100, 2) if myheritage_people else 0
        },
        "in_both_databases": sorted(list(in_both)),
        "only_in_myheritage": sorted(list(only_in_myheritage)),
        "only_in_resilient": sorted(list(only_in_resilient)),
        "pid_name_mapping": {str(pid): list(names) for pid, names in pid_to_names.items()}
    }

    # Save report
    with open('RESILIENT_MYHERITAGE_COMPARISON.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    print(f"People in both databases: {len(in_both)}")
    print(f"Only in MyHeritage: {len(only_in_myheritage)}")
    print(f"Only in Resilient extraction: {len(only_in_resilient)}")
    print(f"Match rate: {report['summary']['match_percentage']}%")

    print("\n" + "="*60)
    print("SAMPLE: Only in MyHeritage (first 10)")
    print("="*60)
    for name in sorted(list(only_in_myheritage))[:10]:
        print(f"  - {name}")

    print("\n" + "="*60)
    print("SAMPLE: Only in Resilient (first 10)")
    print("="*60)
    for name in sorted(list(only_in_resilient))[:10]:
        print(f"  - {name}")

    print("\n" + "="*60)
    print(f"Full report saved to: RESILIENT_MYHERITAGE_COMPARISON.json")
    print("="*60)

if __name__ == "__main__":
    compare_databases()
