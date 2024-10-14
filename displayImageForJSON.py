import tkinter as tk
from tkinter import Label, Button, Frame
from PIL import Image, ImageTk
import json
import os

class StyleViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Style Viewer")

        self.styles = None
        self.current_style_index = 0

        # Frame to display the style content
        self.style_frame = Frame(root)
        self.style_frame.pack(pady=20)

        # Create left and right buttons for navigation
        self.left_button = Button(root, text="<", command=self.previous_style)
        self.left_button.pack(side="left", padx=10)

        self.right_button = Button(root, text=">", command=self.next_style)
        self.right_button.pack(side="right", padx=10)

        # Hard-coded paths
        self.json_file_path = "./static/JSONstyles/style_recommendations.json"
        self.folder_path = "./static/imagesformcam"

        # Load the JSON and display the first style
        self.styles = self.load_json(self.json_file_path)
        self.display_current_style()
        self.update_buttons_state()

    def load_json(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def display_current_style(self):
        self.clear_frame(self.style_frame)
        
        style_key = list(self.styles.keys())[self.current_style_index]
        style_data = self.styles[style_key]

        # Display the image filename
        Label(self.style_frame, text=style_key).pack()

        # Create a frame for the image and its properties
        item_frame = Frame(self.style_frame)
        item_frame.pack(pady=10)

        # Load and display the image
        image_path = os.path.join(self.folder_path, style_key)
        image_label = Label(item_frame)
        self.update_label_image(image_label, image_path)
        image_label.pack()

        # Display the style properties
        properties_text = f"Type: {style_data['type']}\nGender: {style_data['gender']}\nColor: {style_data['color']}\nSeason: {style_data['season']}\nStyle: {style_data['style']}"
        properties_label = Label(item_frame, text=properties_text, justify="left")
        properties_label.pack()

    def update_label_image(self, label, image_path):
        img = Image.open(image_path)
        img = img.resize((100, 100), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(img)
        label.config(image=img)
        label.image = img  # Keep a reference to avoid garbage collection

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def next_style(self):
        if self.styles and self.current_style_index < len(self.styles) - 1:
            self.current_style_index += 1
            self.display_current_style()
            self.update_buttons_state()

    def previous_style(self):
        if self.styles and self.current_style_index > 0:
            self.current_style_index -= 1
            self.display_current_style()
            self.update_buttons_state()

    def update_buttons_state(self):
        if self.styles:
            self.left_button.config(state="normal" if self.current_style_index > 0 else "disabled")
            self.right_button.config(state="normal" if self.current_style_index < len(self.styles) - 1 else "disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = StyleViewerApp(root)
    root.mainloop()
