import customtkinter as ctk
import csv
import re
import textwrap
import mal
import threading
from queue import Queue
import os

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
        
        try:
            episode = self.read_current_episode()
        except FileNotFoundError:
            episode = 1
            self.write_current_episode(episode)
            
        def previous_episode():
            nonlocal episode
            episode -= 1
            if episode < 1:
                episode = 1
                return
            self.update_labels(episode)
            
        def next_episode():
            nonlocal episode
            episode += 1
            if episode > 1105:
                episode = 1105
                return
            self.update_labels(episode)
        
        def update_episode(event):
            nonlocal episode
            if not self.episode_entry.get().isdigit():
                episode_entry_value = self.episode_entry.get()
                episode_entry_value = re.sub(r"\D", "", episode_entry_value)
                self.episode_entry.delete(0, "end")
                self.episode_entry.insert(0, episode_entry_value)
                
            episode = int(self.episode_entry.get())
            if event.type == '38':
                if event.delta > 0:
                    episode += 1
                else:
                    episode -= 1
                    
            if episode < 1:
                episode = 1
            elif episode > 1105:
                episode = 1105           
                    
            self.update_labels(episode)
            self.update_episode_mal(episode)
            
        
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
    
        self.episode_entry.insert(0, str(episode))
        
        self.update_labels(episode)
        
        self.mal_checkbox = ctk.CTkCheckBox(self, text="sync with MAL", command=self.write_mal_sync_state)
        if self.read_mal_sync_state():
            self.mal_checkbox.select()
        self.mal_checkbox.grid(row=4, column=0, columnspan=2, pady=0)
        
        self.mal_update_threads_queue = Queue(20) # TODO: Implement a queue to avoid race conditions
    
    def read_current_episode(self):
        with open("current_episode.txt", "r") as f:
            current_episode = int(f.read())            
        return current_episode

    def write_current_episode(self, current_episode):
        with open("current_episode.txt", "w") as f:
            f.write(f'{current_episode}')
            
    def read_mal_sync_state(self):
        if os.path.exists("mal_sync_state.txt"):
            with open("mal_sync_state.txt", "r") as f:
                mal_sync_state = bool(int(f.read()))
            return mal_sync_state
        
    def write_mal_sync_state(self):
        state = self.mal_checkbox.get()
        with open("mal_sync_state.txt", "w") as f:
            f.write(f'{int(state)}')

    def read_timestamps(self, episode: int):
        with open("times.csv", "r") as f:
            data = csv.DictReader(f)
            for index, row in enumerate(data, start=1):
                if index == episode:
                    return row
                
    def update_labels(self, episode:int):
        episode_data = self.read_timestamps(episode)
        self.episode_entry.delete(0, "end")
        self.episode_entry.insert(0, str(episode))
        
        self.timestamp_label.configure(text=episode_data["start_time"] if episode_data["start_time"] else episode_data["title_card_time"])
        comment = episode_data["comment"]
        comment = textwrap.fill(comment, width=30)
        
        self.comment_label.configure(text=comment)
        self.write_current_episode(episode)
        
    def _update_episode_mal(self, episode):
        token = mal.get_token()["access_token"] 
        mal.update_one_piece_episode(token, episode) 
        
    def update_episode_mal(self, episode):
        if not self.mal_checkbox.get():
            return
              
        thread = threading.Thread(target=self._update_episode_mal, args=(episode,))
        thread.start()
                


if __name__ == "__main__":
    app = OnePieceTimestamps()
    app.mainloop()