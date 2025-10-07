#!/usr/bin/env python3
"""
Resilient Saikura Family Extractor
Uses multiple strategies to extract family data despite CAPTCHA blocks
"""

from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import random


class ResilientSaikuraExtractor:
    def __init__(self):
        self.driver = None
        self.all_people = {}
        self.session_established = False
        
    def setup_driver(self):
        """Setup Chrome WebDriver with stealth options"""
        chrome_options = Options()
        # Add stealth options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("Chrome browser opened with stealth settings")
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            raise
    
    def try_establish_session(self):
        """Try to establish a working session by accessing the site"""
        print("Attempting to establish session with the site...")

        # Try the homepage first
        self.driver.get("https://saikura.tribalpages.com/tribe/browse?userid=saikura&view=9")
        time.sleep(5)

        # Check if we need CAPTCHA
        title = self.driver.title
        if "TribalPages Security" in title:
            print("CAPTCHA detected. Waiting 20 seconds for manual resolution...")
            print("Please solve the CAPTCHA in the browser window NOW!")

            # Wait exactly 20 seconds for CAPTCHA resolution
            for i in range(20):
                time.sleep(1)
                try:
                    current_title = self.driver.title
                    if "TribalPages Security" not in current_title:
                        print("CAPTCHA resolved! Session established.")
                        self.session_established = True
                        return True
                except:
                    pass

                if i % 5 == 0 and i > 0:
                    print(f"  {20 - i} seconds remaining...")

            # Check one final time
            try:
                if "TribalPages Security" not in self.driver.title:
                    print("CAPTCHA resolved! Session established.")
                    self.session_established = True
                    return True
            except:
                pass

            print("CAPTCHA not resolved in time. Attempting to continue...")
            return False
        else:
            print("No CAPTCHA detected. Session ready.")
            self.session_established = True
            return True
    
    def resilient_extract_person(self, pid):
        """Extract person data with multiple retry strategies"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Random delay to avoid detection
                time.sleep(random.uniform(1, 3))
                
                url = f"https://saikura.tribalpages.com/tribe/browse?userid=saikura&view=0&pid={pid}"
                self.driver.get(url)
                time.sleep(2)
                
                # Check for CAPTCHA
                if "TribalPages Security" in self.driver.title:
                    print(f"  Person {pid}: CAPTCHA block on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        # Wait longer between retries
                        time.sleep(30)
                        continue
                    else:
                        return "BLOCKED"
                
                # Check if valid person page
                page_source = self.driver.page_source
                if len(page_source) < 2000 or "Person not found" in page_source:
                    return "NOT_FOUND"
                
                # Parse person data
                person_data = self.parse_person_page(pid, page_source)
                return person_data
                
            except Exception as e:
                print(f"  Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                else:
                    return None
        
        return None
    
    def parse_person_page(self, pid, page_source):
        """Parse person page for detailed information"""
        tree = html.fromstring(page_source)
        
        person_data = {
            'pid': pid,
            'name': None,
            'birth_date': None,
            'death_date': None,
            'gender': None,
            'father': None,
            'mother': None,
            'spouse': None,
            'children': [],
            'photos': [],
            'additional_info': {}
        }
        
        # Extract name from page title
        title = self.driver.title
        if " - " in title and "Family Tree" in title:
            name_part = title.split(" - ")[0].strip()
            if name_part and len(name_part) > 2 and "Security" not in name_part:
                person_data['name'] = name_part
        
        # Extract all text for analysis
        all_text = ' '.join(tree.xpath("//text()"))
        
        # Extract family relationships
        family_links = tree.xpath("//a[contains(@href, 'view=0&pid=')]")
        for link in family_links:
            href = link.get('href', '')
            name = link.text or ''
            if name and href and 'pid=' in href:
                related_pid_match = re.search(r'pid=(\d+)', href)
                if related_pid_match:
                    related_pid = int(related_pid_match.group(1))
                    if related_pid != pid:
                        person_data['children'].append({
                            'name': name.strip(),
                            'pid': related_pid
                        })
        
        # Extract birth date
        birth_patterns = [
            r'born[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            r'birth[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            r'born[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'born[:\s]*(\d{4})'
        ]
        
        for pattern in birth_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                person_data['birth_date'] = match.group(1)
                break
        
        # Extract death date
        death_patterns = [
            r'died[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            r'death[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
            r'died[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'died[:\s]*(\d{4})'
        ]
        
        for pattern in death_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                person_data['death_date'] = match.group(1)
                break
        
        # Extract photos
        img_elements = tree.xpath("//img[contains(@src, 'photo') or contains(@src, 'saikura')]")
        for img in img_elements:
            src = img.get('src', '')
            if src and 'saikura' in src:
                person_data['photos'].append(src)
        
        return person_data
    
    def resilient_full_extraction(self):
        """Main extraction method with resilience strategies"""
        print("Starting Resilient Saikura Family Extraction")
        print("=" * 60)
        
        if not self.driver:
            self.setup_driver()
        
        # Try to establish session
        if not self.try_establish_session():
            print("Could not establish session. Continuing with limited extraction...")
        
        # Use all possible PIDs to find the 181 family members
        print("Starting systematic extraction of all family members...")
        all_pids = list(range(1, 201))  # PIDs 1-200 to capture all 181 people
        
        successful_extractions = 0
        blocked_count = 0
        not_found_count = 0
        
        for i, pid in enumerate(all_pids):
            print(f"Processing person {pid} ({i+1}/{len(all_pids)})...")
            
            result = self.resilient_extract_person(pid)
            
            if result == "BLOCKED":
                blocked_count += 1
                print(f"  BLOCKED (total blocks: {blocked_count})")
                
                # If too many blocks, take a longer break
                if blocked_count % 10 == 0:
                    print(f"Taking a 60-second break after {blocked_count} blocks...")
                    time.sleep(60)
                    
            elif result == "NOT_FOUND":
                not_found_count += 1
                print("  Not found")
                
            elif result:
                self.all_people[pid] = result
                successful_extractions += 1
                name = result.get('name', 'Unknown')
                connections = len(result.get('children', []))
                print(f"  SUCCESS: {name} ({connections} connections)")
                blocked_count = 0  # Reset block counter on success
            
            # Progress update
            if (i + 1) % 25 == 0:
                print(f"\nPROGRESS: {i+1}/{len(all_pids)} checked")
                print(f"  Successful: {successful_extractions}")
                print(f"  Blocked: {blocked_count}")
                print(f"  Not found: {not_found_count}")
        
        print(f"\nExtraction complete!")
        print(f"Successfully extracted {successful_extractions} family members")
        print(f"Total blocks encountered: {blocked_count}")
        
        # Save results
        self.save_complete_database()
        
        return self.all_people
    
    def save_complete_database(self):
        """Save the complete Saikura family database"""
        output = {
            "extraction_date": "2025-10-04",
            "family_name": "Saikura Family Tree - Resilient Extraction",
            "extraction_method": "Resilient multi-strategy extraction",
            "total_people_extracted": len(self.all_people),
            "people": {}
        }
        
        # Convert to string keys for JSON
        for pid, person_data in self.all_people.items():
            output["people"][str(pid)] = person_data
        
        # Save main database
        with open("SAIKURA_RESILIENT_FAMILY_DATABASE.json", "w", encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        # Create detailed summary
        people_with_names = [p for p in self.all_people.values() if p.get('name')]
        people_with_births = [p for p in self.all_people.values() if p.get('birth_date')]
        people_with_deaths = [p for p in self.all_people.values() if p.get('death_date')]
        people_with_photos = [p for p in self.all_people.values() if p.get('photos')]
        
        summary = {
            "extraction_summary": {
                "total_people": len(self.all_people),
                "people_with_names": len(people_with_names),
                "people_with_birth_dates": len(people_with_births),
                "people_with_death_dates": len(people_with_deaths),
                "people_with_photos": len(people_with_photos),
                "total_family_connections": sum(len(p.get('children', [])) for p in self.all_people.values())
            },
            "sample_people": [
                {
                    "pid": p['pid'],
                    "name": p.get('name', 'Unknown'),
                    "birth_date": p.get('birth_date'),
                    "connections": len(p.get('children', []))
                }
                for p in people_with_names[:10]
            ]
        }
        
        with open("SAIKURA_RESILIENT_SUMMARY.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n*** RESILIENT SAIKURA FAMILY DATABASE COMPLETE! ***")
        print(f"File saved: SAIKURA_RESILIENT_FAMILY_DATABASE.json")
        print(f"Total people: {len(self.all_people)}")
        print(f"People with names: {len(people_with_names)}")
        print(f"People with birth dates: {len(people_with_births)}")
        print(f"People with death dates: {len(people_with_deaths)}")
        print(f"People with photos: {len(people_with_photos)}")
    
    def close_browser(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


def main():
    extractor = ResilientSaikuraExtractor()
    
    try:
        print("RESILIENT SAIKURA FAMILY EXTRACTION")
        print("=" * 60)
        print("This will attempt to extract ALL family members using resilient strategies.")
        print("Please be ready to solve CAPTCHAs when they appear.")
        print("=" * 60)
        
        result = extractor.resilient_full_extraction()
        
        print(f"\n*** RESILIENT EXTRACTION COMPLETE! ***")
        print(f"Successfully extracted {len(result)} Saikura family members")
        print("Check SAIKURA_RESILIENT_FAMILY_DATABASE.json for complete data")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        
    finally:
        print("\nClosing browser in 10 seconds...")
        time.sleep(10)
        extractor.close_browser()


if __name__ == "__main__":
    main()