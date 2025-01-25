import json
from datetime import datetime
import requests
import os
import re

JSONBIN_URL = "https://api.jsonbin.io/v3/b"
API_KEY = "$2a$10$rdg9ul795TeIEwpinuWAtO..Q3qmkklWJM5wwgUARUo/Y1/A91XoK"  # Replace with YOUR actual X-Master-Key
METADATA_FILE = "diary_metadata.json"


class DiaryEntry:
    def __init__(self, title, description, date_str=None):
        self.title = title
        self.description = description
        if date_str:
            self.date = date_str
        else:
            self.date = str(datetime.now())  # Store current date and time

    def to_dict(self):
        """Convert diary entry to a dictionary for JSON serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a DiaryEntry from a dictionary (used when loading from JSON)."""
        return cls(data["title"], data["description"], data["date"])


    def save(self):
        """Saves the diary entry to JSONBin and returns the URL."""
        json_data = json.dumps(self.to_dict(), indent=4)
        try:
            headers = {
                'Content-Type': 'application/json',
                 "X-Master-Key": f"{API_KEY}"
            }
            response = requests.post(JSONBIN_URL, headers=headers, data=json_data)
            response.raise_for_status()
            bin_id = response.json()['metadata']['id']
            return f"https://jsonbin.io/{bin_id}"
        except requests.exceptions.RequestException as e:
            print(f"Error saving to JSONBin: {e}")
            return None

    @staticmethod
    def load(url):
        """Loads a diary entry from a JSONBin URL."""
        try:
            bin_id = url.split("/")[-1]
            headers = {
                 "X-Master-Key": f"{API_KEY}",
                'Content-Type': 'application/json'
            }
            response = requests.get(f"{JSONBIN_URL}/{bin_id}", headers=headers)
            response.raise_for_status()
            data = response.json()['record']
            return [DiaryEntry.from_dict(data)]
        except requests.exceptions.RequestException as e:
            print(f"Error loading from JSONBin: {e}")
            return None
        except KeyError as e:
          print(f"Error loading from JSONBin: Invalid data returned.")
          return None


def load_metadata():
    """Loads diary metadata from the local JSON file."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_metadata(metadata):
    """Saves diary metadata to the local JSON file."""
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)


def create_new_entry():
    title = input("Enter diary entry title: ")
    description = input("Enter your entry: ")
    entry = DiaryEntry(title, description)
    url = entry.save()
    if url:
       print(f"Entry saved to {url}")
       metadata = load_metadata()
       if title in metadata:
            print("Warning: An entry with this title already exists, it will overwrite the old value.")
       metadata[title] = url
       save_metadata(metadata)


def read_entry():
    metadata = load_metadata()
    if not metadata:
        print("No entries found")
        return

    titles = list(metadata.keys())
    print("\nSelect an entry to read:")
    for i, title in enumerate(titles):
        print(f"{i + 1}. {title}")

    while True:
        try:
            choice = int(input("Enter the number of the entry: "))
            if 1 <= choice <= len(titles):
                selected_title = titles[choice - 1]
                break
            else:
                print("Invalid entry number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    url = metadata.get(selected_title)
    if url:
        entries = DiaryEntry.load(url)
        if entries:
            print("\n--- Diary Entries ---")
            for entry in entries:
                print(f"Title: {entry.title}")
                print(f"Date: {entry.date}")
                print(f"Description: {entry.description}")
                print("---")
        else:
            print("Error loading entry from URL")
    else:
        print("Entry not found in metadata.")


def edit_entry():
    metadata = load_metadata()
    if not metadata:
        print("No entries found")
        return
    
    titles = list(metadata.keys())
    print("\nSelect an entry to edit:")
    for i, title in enumerate(titles):
       print(f"{i + 1}. {title}")
    
    while True:
        try:
            choice = int(input("Enter the number of the entry to edit: "))
            if 1 <= choice <= len(titles):
                selected_title = titles[choice - 1]
                break
            else:
                print("Invalid entry number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    url = metadata.get(selected_title)
    if url:
        entries = DiaryEntry.load(url)
        if entries:
            entry = entries[0]
            print("Current entry:")
            print(f"Title: {entry.title}")
            print(f"Date: {entry.date}")
            print(f"Description: {entry.description}")
    
            new_description = input("Enter the new entry description, leave blank to keep the old value: ")
            if new_description.strip():
                entry.description = new_description
            
            new_title = input("Enter the new entry title, leave blank to keep the old value: ")
            if new_title.strip():
                if new_title in metadata and new_title != selected_title:
                    print("Warning: An entry with this title already exists, it will overwrite the old value.")
                del metadata[selected_title]
                metadata[new_title] = url
                entry.title = new_title
                
            entry.date = str(datetime.now())
            
            url = entry.save()
            if url:
                print(f"Entry updated and saved to {url}")
                save_metadata(metadata)
        else:
            print("Error loading entry from URL")
    else:
      print("Entry not found in metadata.")


def search_entry():
    metadata = load_metadata()
    if not metadata:
        print("No entries found")
        return

    search_term = input("Enter the search term: ")
    
    matches = []
    for title, url in metadata.items():
            if re.search(search_term, title, re.IGNORECASE):
                matches.append(title)
                continue
            entries = DiaryEntry.load(url)
            if entries and any(re.search(search_term, entry.description, re.IGNORECASE) for entry in entries):
                matches.append(title)

    if matches:
        print("\nMatching entries:")
        for i, title in enumerate(matches):
            print(f"{i + 1}. {title}")
    else:
        print("No matching entries found")


def main():
    while True:
        print("\nDiary Application")
        print("1. Create new entry")
        print("2. Read an entry")
        print("3. Edit an entry")
        print("4. Search for entry")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_new_entry()
        elif choice == "2":
            read_entry()
        elif choice == "3":
            edit_entry()
        elif choice == "4":
            search_entry()
        elif choice == "5":
            print("Goodbye")
            break
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    main()