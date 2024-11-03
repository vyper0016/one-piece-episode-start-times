import customtkinter as ctk
import csv
import re
import textwrap
import mal
import threading
from queue import Queue
import os
import pickle

LAST_EP = 1105  # TODO get this from the csv file, update csv every week
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

class OnePieceTimestamps(ctk.CTk):
    def __init__(self):
        super().__init__()
        HEIGHT = 180
        WIDTH = 230

        self.geometry(f"{WIDTH}x{HEIGHT}")
        self.title("One Piece Timestamps")
        self.resizable(False, False)
        self.iconbitmap("icon.ico")
        
        if os.path.exists('vars.pkl'):
            with open('vars.pkl', 'rb') as f:
                self.current_episode, self.mal_state = pickle.load(f)
        else:
            self.current_episode = 1
            self.mal_state = False

            
        def previous_episode():
            self.current_episode -= 1
            if self.current_episode < 1:
                self.current_episode = 1
                return
            self.update_labels()
            
        def next_episode():
            self.current_episode += 1
            if self.current_episode > LAST_EP:
                self.current_episode = 1105
                return
            self.update_labels()
        
        def update_episode(event):
            if not self.episode_entry.get().isdigit():
                episode_entry_value = self.episode_entry.get()
                episode_entry_value = re.sub(r"\D", "", episode_entry_value)
                self.episode_entry.delete(0, "end")
                self.episode_entry.insert(0, episode_entry_value)
                
            self.current_episode = int(self.episode_entry.get())
            if event.type == '38':
                if event.delta > 0:
                    self.current_episode += 1
                else:
                    self.current_episode -= 1
                    
            if self.current_episode < 1:
                self.current_episode = 1
            elif self.current_episode > 1105:
                self.current_episode = 1105           
                    
            self.update_labels()
            
        def make_widgets():
            episode_label = ctk.CTkLabel(self, text=f"episode:")
            episode_label.grid(row=0, column=0, pady=10, padx=5, sticky="e")
            episode_label.configure(font=("Arial", 14))
            
            self.episode_entry = ctk.CTkEntry(self, width=70)
            self.episode_entry.grid(row=0, column=1, pady=10, padx=5, sticky="w")
            self.episode_entry.configure(font=("Arial", 14))    
            
            self.timestamp_label = ctk.CTkLabel(self, text="")
            self.timestamp_label.grid(row=1, column=0, columnspan=2, padx=15)
            self.timestamp_label.configure(font=("Arial", 25))
            
            self.comment_label = ctk.CTkLabel(self, text="")
            self.comment_label.grid(row=2, column=0, columnspan=2, padx=10)
            self.comment_label.configure(font=("Arial", 14))
            
            previous_button = ctk.CTkButton(self, text="Previous", command=previous_episode, width=100)
            previous_button.grid(row=3, column=0, pady=10, padx=7)
            
            next_button = ctk.CTkButton(self, text="Next", command=next_episode, width=100)
            next_button.grid(row=3, column=1, pady=10, padx=7)
            
            self.episode_entry.bind("<KeyRelease>", update_episode)
            self.bind("<MouseWheel>", update_episode)
        
            self.episode_entry.insert(0, str(self.current_episode))
        
        make_widgets()
        self.after(15, self.update_labels)
        
        self.mal_checkbox = ctk.CTkCheckBox(self, text="sync with MAL", command=self.write_mal_sync_state)
        if self.mal_state:
            self.mal_checkbox.select()
        self.mal_checkbox.grid(row=4, column=0, columnspan=2, pady=0)
        
        self.mal_update_threads_queue = Queue(20) # TODO: Implement a queue to avoid race conditions
       
    def write_mal_sync_state(self):
        self.mal_state = self.mal_checkbox.get()
        self.update_episode_mal()
        self.update_vars()

    def update_vars(self):
        with open('vars.pkl', 'wb') as f:
            pickle.dump([self.current_episode, self.mal_state], f)
    
    def read_timestamps(self, episode: int):
        with open("times.csv", "r") as f:
            data = csv.DictReader(f)
            for index, row in enumerate(data, start=1):
                if index == episode:
                    return row
                
    def update_labels(self):
        episode_data = self.read_timestamps(self.current_episode)
        self.episode_entry.delete(0, "end")
        self.episode_entry.insert(0, str(self.current_episode))
        
        self.timestamp_label.configure(text=episode_data["start_time"] if episode_data["start_time"] else episode_data["title_card_time"])
        comment = episode_data["comment"]
        comment = textwrap.fill(comment, width=30)
        
        self.comment_label.configure(text=comment)
        self.update_vars()
        self.update_episode_mal()
        
    def _update_episode_mal(self, episode):
        token = mal.get_token()["access_token"] 
        mal.update_one_piece_episode(token, episode) 
        
    def update_episode_mal(self):
        if not self.mal_checkbox.get():
            return
              
        thread = threading.Thread(target=self._update_episode_mal, args=(self.current_episode,))
        thread.start()
                

if __name__ == "__main__":
    app = OnePieceTimestamps()
    app.mainloop()