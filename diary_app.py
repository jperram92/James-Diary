import json
from datetime import datetime
import requests
import os
import re
import tkinter as tk
from tkinter import scrolledtext, font

JSONBIN_URL = "https://api.jsonbin.io/v3/b"
API_KEY = "$2a$10$rdg9ul795TeIEwpinuWAtO..Q3qmkklWJM5wwgUARUo/Y1/A91XoK"  # Replace with your API Key
METADATA_FILE = "diary_metadata.json"


class DiaryEntry:
    def __init__(self, title, description, date_str=None):
        self.title = title
        self.description = description
        if date_str:
            self.date = date_str
        else:
            self.date = str(datetime.now())

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


def create_new_entry_gui(entries_frame):
    def create_entry():
        title = title_entry.get()
        description = description_text.get("1.0", tk.END).strip()
        if title and description:
            entry = DiaryEntry(title, description)
            url = entry.save()
            if url:
                metadata = load_metadata()
                if title in metadata:
                  print("Warning: An entry with this title already exists, it will overwrite the old value.")
                metadata[title] = url
                save_metadata(metadata)
                update_entries(entries_frame)
                new_entry_window.destroy()
        else:
            print("Both title and description are required")
           
    new_entry_window = tk.Toplevel()
    new_entry_window.title("Create New Entry")
    
    tk.Label(new_entry_window, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    title_entry = tk.Entry(new_entry_window)
    title_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    
    tk.Label(new_entry_window, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    description_text = scrolledtext.ScrolledText(new_entry_window, height=10)
    description_text.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)
    
    tk.Button(new_entry_window, text="Save Entry", command=create_entry).grid(row=2, column=0, columnspan=2, pady=10)
    new_entry_window.grid_columnconfigure(1, weight=1)
    new_entry_window.grid_rowconfigure(1, weight=1)

def update_entries(entries_frame, search_matches=None):
     for widget in entries_frame.winfo_children():
            widget.destroy()
     metadata = load_metadata()
     if not metadata:
         tk.Label(entries_frame, text="No Entries Yet!").pack()
         return

     for i, (title, url) in enumerate(metadata.items()):
        if search_matches is None or title in search_matches:
          try:
            entries = DiaryEntry.load(url)
            if entries:
              entry = entries[0]
              text = f"{entry.title}\n{entry.date}\n{entry.description}"

              text_widget = scrolledtext.ScrolledText(entries_frame, wrap=tk.WORD, height=10, width=40, borderwidth=2, relief="groove")
              text_widget.insert(tk.END, text)
              text_widget.config(state=tk.DISABLED)
              text_widget.grid(row=i//2, column=i%2, padx=5, pady=5)
          except Exception as e:
             print (f"Error loading entries:{e}")

def edit_entry_gui(entries_frame):
    def edit_selected_entry():
        selected_title = titles[entry_list.curselection()[0]]
        
        url = metadata.get(selected_title)
        if url:
                entries = DiaryEntry.load(url)
                if entries:
                    entry = entries[0]
                    
                    edit_window = tk.Toplevel()
                    edit_window.title(f"Edit {entry.title}")
                    
                    tk.Label(edit_window, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
                    title_entry = tk.Entry(edit_window)
                    title_entry.insert(0, entry.title)
                    title_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
                    
                    tk.Label(edit_window, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
                    description_text = scrolledtext.ScrolledText(edit_window, height=10)
                    description_text.insert(tk.END, entry.description)
                    description_text.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=5)

                    def save_changes():
                        nonlocal url #allows us to modify the url variable in the outer function.
                        new_description = description_text.get("1.0", tk.END).strip()
                        if new_description.strip():
                            entry.description = new_description
                        
                        new_title = title_entry.get()
                        
                        if new_title.strip() and new_title != selected_title : # Only attempt to delete if the title has changed.
                           if new_title in metadata:
                                print("Warning: An entry with this title already exists, it will overwrite the old value.")
                           del metadata[selected_title]
                           metadata[new_title] = url # This now must be a new url
                           entry.title = new_title
                        
                        
                        entry.date = str(datetime.now())
                        url = entry.save() # Re-save, to ensure metadata changes are saved.
                        if url:
                            print(f"Entry updated and saved to {url}")
                            save_metadata(metadata)
                            update_entries(entries_frame)
                            edit_window.destroy()
                        
                    tk.Button(edit_window, text="Save Changes", command=save_changes).grid(row=2, column=0, columnspan=2, pady=10)
                    edit_window.grid_columnconfigure(1, weight=1)
                    edit_window.grid_rowconfigure(1, weight=1)
                else:
                    print("Error loading entry from URL")
        else:
            print("Entry not found in metadata.")

    metadata = load_metadata()
    if not metadata:
        print("No entries found")
        return

    titles = list(metadata.keys())
    
    edit_window = tk.Toplevel()
    edit_window.title("Edit Entry")
    
    tk.Label(edit_window, text="Select an entry to edit:").pack()
    entry_list = tk.Listbox(edit_window)
    entry_list.pack()
    for i, title in enumerate(titles):
        entry_list.insert(tk.END, title)
    
    tk.Button(edit_window, text="Edit Entry", command=edit_selected_entry).pack()

def search_entry_gui(entries_frame):
    def search():
        search_term = search_entry.get()
        if not search_term:
            print("Search term cannot be blank")
            return
        matches = []
        for title, url in metadata_inner.items():
            if re.search(search_term, title, re.IGNORECASE):
                matches.append(title)
                continue
            entries = DiaryEntry.load(url)
            if entries and any(re.search(search_term, entry.description, re.IGNORECASE) for entry in entries):
                matches.append(title)

        update_entries(entries_frame, search_matches=matches)
        search_window.destroy()
    
    metadata_inner = load_metadata() # load the metadata from the correct function
    search_window = tk.Toplevel()
    search_window.title("Search Entries")
    tk.Label(search_window, text="Enter the search term:").pack()
    search_entry = tk.Entry(search_window)
    search_entry.pack()
    tk.Button(search_window, text="Search", command=search).pack()
    
def delete_entry_gui(entries_frame):
    def delete_selected_entry():
        if entry_list.curselection():
          selected_title = titles[entry_list.curselection()[0]]

          if selected_title in metadata:
             url = metadata[selected_title]
             try:
                headers = {
                    'Content-Type': 'application/json',
                     "X-Master-Key": f"{API_KEY}"
                   }
                requests.put(url, headers=headers, data="{}") # Delete by sending an empty data object
                
                del metadata[selected_title]
                save_metadata(metadata)
                update_entries(entries_frame)
                delete_window.destroy()
             except requests.exceptions.RequestException as e:
                print(f"Error deleting from JSONBin: {e}")
          else:
              print("Error: Entry not found in metadata.")
        else:
              print("Error: Please select an entry first")

    metadata = load_metadata()
    if not metadata:
        print("No entries found")
        return

    titles = list(metadata.keys())
    
    delete_window = tk.Toplevel()
    delete_window.title("Delete Entry")
    
    tk.Label(delete_window, text="Select an entry to delete:").pack()
    entry_list = tk.Listbox(delete_window)
    entry_list.pack()
    for i, title in enumerate(titles):
        entry_list.insert(tk.END, title)
    
    tk.Button(delete_window, text="Delete Entry", command=delete_selected_entry).pack()
    
def main():
    root = tk.Tk()
    root.title("My Diary")
    
    entries_frame = tk.Frame(root)
    entries_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    create_button = tk.Button(button_frame, text="Create New Entry", command=lambda: create_new_entry_gui(entries_frame))
    create_button.pack(side=tk.LEFT, padx=5)
    
    edit_button = tk.Button(button_frame, text="Edit Entry", command=lambda: edit_entry_gui(entries_frame))
    edit_button.pack(side=tk.LEFT, padx=5)
    
    search_button = tk.Button(button_frame, text="Search Entry", command=lambda: search_entry_gui(entries_frame))
    search_button.pack(side=tk.LEFT, padx=5)
    
    delete_button = tk.Button(button_frame, text="Delete Entry", command=lambda: delete_entry_gui(entries_frame))
    delete_button.pack(side=tk.LEFT, padx=5)
    
    update_entries(entries_frame)

    root.mainloop()
    
if __name__ == "__main__":
    main()