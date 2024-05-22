import customtkinter as ctk
import csv
import re
import textwrap

ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

HEIGHT = 155
WIDTH = 230

def read_current_episode():
    with open("current_episode.txt", "r") as f:
        current_episode = int(f.read())
        
    return current_episode

def write_current_episode(current_episode):
    with open("current_episode.txt", "w") as f:
        f.write(str(current_episode))

def read_timestamps(episode: int):
    with open("times.csv", "r") as f:
        data = csv.DictReader(f)
        for index, row in enumerate(data, start=1):
            if index == episode:
                return row
            
def update_labels(episode_entry, timestamp_label, comment_label, episode:int):
    episode_data = read_timestamps(episode)
    episode_entry.delete(0, "end")
    episode_entry.insert(0, str(episode))
    
    timestamp_label.configure(text=episode_data["start_time"] if episode_data["start_time"] else episode_data["title_card_time"])
    comment = episode_data["comment"]
    comment = textwrap.fill(comment, width=30)
    
    comment_label.configure(text=comment)
    write_current_episode(episode)

def main():
    app = ctk.CTk()
    app.geometry(f"{WIDTH}x{HEIGHT}")
    app.title("One Piece Timestamps")
    app.resizable(False, False)
    
    try:
        episode = read_current_episode()
    except FileNotFoundError:
        episode = 1
        write_current_episode(episode)
        
    def previous_episode():
        nonlocal episode
        episode -= 1
        if episode < 1:
            episode = 1
            return
        update_labels(episode_entry, timestamp_label, comment_label, episode)
        
    def next_episode():
        nonlocal episode
        episode += 1
        if episode > 1105:
            episode = 1105
            return
        update_labels(episode_entry, timestamp_label, comment_label, episode)
    
    def update_episode(event):
        nonlocal episode
        if not episode_entry.get().isdigit():
            episode_entry_value = episode_entry.get()
            episode_entry_value = re.sub(r"\D", "", episode_entry_value)
            episode_entry.delete(0, "end")
            episode_entry.insert(0, episode_entry_value)
            
        episode = int(episode_entry.get())
        if event.type == '38':
            if event.delta > 0:
                episode += 1
            else:
                episode -= 1
                
        if episode < 1:
            episode = 1
        elif episode > 1105:
            episode = 1105
        
                
        update_labels(episode_entry, timestamp_label, comment_label, episode)
        
    
    episode_label = ctk.CTkLabel(app, text=f"episode:")
    episode_label.grid(row=0, column=0, pady=10, padx=5, sticky="e")
    episode_label.configure(font=("Arial", 14))
    
    episode_entry = ctk.CTkEntry(app, width=70)
    episode_entry.grid(row=0, column=1, pady=10, padx=5, sticky="w")
    episode_entry.configure(font=("Arial", 14))    
    
    timestamp_label = ctk.CTkLabel(app, text="")
    timestamp_label.grid(row=1, column=0, columnspan=2, padx=15)
    timestamp_label.configure(font=("Arial", 25))
    
    comment_label = ctk.CTkLabel(app, text="")
    comment_label.grid(row=2, column=0, columnspan=2, padx=10)
    comment_label.configure(font=("Arial", 14))
    
    previous_button = ctk.CTkButton(app, text="Previous", command=previous_episode, width=100)
    previous_button.grid(row=3, column=0, pady=10, padx=7)
    
    next_button = ctk.CTkButton(app, text="Next", command=next_episode, width=100)
    next_button.grid(row=3, column=1, pady=10, padx=7)
    
    episode_entry.bind("<KeyRelease>", update_episode)
    app.bind("<MouseWheel>", update_episode)
   
    episode_entry.insert(0, str(episode))
    
    update_labels(episode_entry, timestamp_label, comment_label, episode)
    

    app.mainloop()    

if __name__ == "__main__":
    main()