import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageDisplayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Group Display App")
        
        # Frame for buttons
        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        self.load_json_button = tk.Button(frame, text="Load JSON File", command=self.load_json)
        self.load_json_button.pack(side=tk.LEFT, padx=10)

        self.load_folder_button = tk.Button(frame, text="Load Image Folder", command=self.load_folder)
        self.load_folder_button.pack(side=tk.LEFT, padx=10)

        self.prev_button = tk.Button(frame, text="Previous Group", command=self.show_previous_group, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(frame, text="Next Group", command=self.show_next_group, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.quit_button = tk.Button(frame, text="Quit", command=self.root.quit)
        self.quit_button.pack(side=tk.LEFT, padx=10)

        # Frame for displaying images and metadata
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=20)

        self.group_label = tk.Label(self.image_frame, text="", font=("Arial", 16))
        self.group_label.pack(pady=10)

        self.metadata_label = tk.Label(self.image_frame, text="", font=("Arial", 12))
        self.metadata_label.pack(pady=10)

        self.image_labels = [tk.Label(self.image_frame) for _ in range(3)]
        for label in self.image_labels:
            label.pack(side=tk.LEFT, padx=10)

        self.json_data = None
        self.folder_path = None
        self.current_group_index = 0
        self.group_names = []

    def load_json(self):
        json_file_path = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
        if json_file_path:
            with open(json_file_path, 'r') as json_file:
                self.json_data = json.load(json_file)
                self.group_names = list(self.json_data.keys())
                self.current_group_index = 0
            messagebox.showinfo("Success", "JSON file loaded successfully.")
            self.update_buttons()

    def load_folder(self):
        self.folder_path = filedialog.askdirectory(title="Select Image Folder")
        if self.folder_path:
            if not self.json_data:
                messagebox.showwarning("Warning", "Please load a JSON file first.")
                return
            self.display_group_and_metadata(self.current_group_index)

    def display_group_and_metadata(self, group_index):
        if not self.group_names:
            return

        group_name = self.group_names[group_index]
        items = self.json_data[group_name]

        self.group_label.config(text=f"Group: {group_name}")

        metadata_text = ""
        image_files = list(items.keys())
        
        for i, image_name in enumerate(image_files):
            metadata = items[image_name]
            metadata_text += f"Image: {image_name}\n"
            metadata_text += f"Type: {metadata['type']}, Gender: {metadata['gender']}, Color: {metadata['color']}, Season: {metadata['season']}, Style: {metadata['style']}\n\n"
            
            if i < len(self.image_labels):
                image_path = os.path.join(self.folder_path, image_name)
                if os.path.isfile(image_path):
                    # Display the image
                    image = Image.open(image_path)
                    image = image.resize((150, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.image_labels[i].config(image=photo)
                    self.image_labels[i].image = photo  # Keep a reference to avoid garbage collection
                else:
                    self.image_labels[i].config(image=None)
                    self.image_labels[i].image = None
            else:
                break

        self.metadata_label.config(text=metadata_text)
        self.update_buttons()

    def show_next_group(self):
        if self.current_group_index < len(self.group_names) - 1:
            self.current_group_index += 1
            self.display_group_and_metadata(self.current_group_index)

    def show_previous_group(self):
        if self.current_group_index > 0:
            self.current_group_index -= 1
            self.display_group_and_metadata(self.current_group_index)

    def update_buttons(self):
        if self.current_group_index == 0:
            self.prev_button.config(state=tk.DISABLED)
        else:
            self.prev_button.config(state=tk.NORMAL)

        if self.current_group_index == len(self.group_names) - 1:
            self.next_button.config(state=tk.DISABLED)
        else:
            self.next_button.config(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = ImageDisplayApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
