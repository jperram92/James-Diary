import json
from datetime import date
import requests
import os

JSONBIN_URL = "https://api.jsonbin.io/v3/b" # Base URL for JSONBin
API_KEY = "$2a$10$rdg9ul795TeIEwpinuWAtO..Q3qmkklWJM5wwgUARUo/Y1/A91XoK"  # Replace with your X-Master-Key
METADATA_FILE = "diary_metadata.json"


class DiaryEntry:
    def __init__(self, title, description, date_str=None):
        self.title = title
        self.description = description
        if date_str:
          self.date = str(date_str)
        else:
          self.date = str(date.today())  # Ensure date is always a string

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
                 "X-Master-Key": f"{API_KEY}" # Using the Master-Key for saving
            }
            response = requests.post(JSONBIN_URL, headers=headers, data=json_data)
            response.raise_for_status() # Raise exception if the response status is 4XX or 5XX
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
            return DiaryEntry.from_dict(data)
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
        entry = DiaryEntry.load(url)
        if entry:
            print("\n--- Diary Entry ---")
            print(f"Title: {entry.title}")
            print(f"Date: {entry.date}")
            print(f"Description: {entry.description}")
        else:
            print("Error loading entry from URL")
    else:
        print("Entry not found in metadata.")


def main():
    while True:
        print("\nDiary Application")
        print("1. Create new entry")
        print("2. Read an entry")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_new_entry()
        elif choice == "2":
            read_entry()
        elif choice == "3":
            print("Goodbye")
            break
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    main()