import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
import os
import subprocess
import sys
import urllib.request
import webbrowser
import io

# ✅ Add NEWSAPP root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try to import ThemedStyle for modern appearance
try:
    from ttkthemes import ThemedStyle
except ImportError:
    ThemedStyle = None

# ✅ Import the detailed scrapers
from modules.economictimes.scrape_et_detail_by_index import scrape_single_et_article
from modules.thehindu.scrape_th_detail_by_index import scrape_single_th_article
from modules.indianexpress.scrape_ie_detail_by_index import scrape_single_ie_article
from modules.timesofindia.scrape_toi_detail_by_index import scrape_single_toi_article


class NewsApp:
    def __init__(self, root):
        # Configure the root window for fade effect
        self.root = root
        self.root.withdraw()
        self.fade_alpha = 0.0
        self.root.attributes("-alpha", self.fade_alpha)
        self.root.deiconify()
        self.root.title("The News App")

        # Apply modern theme if available
        if ThemedStyle:
            self.style = ThemedStyle(self.root)
            self.style.set_theme("arc")
        else:
            self.style = ttk.Style(self.root)
            self.style.theme_use("clam")

        # Start the welcome screen
        self.show_welcome_screen()

    def show_welcome_screen(self):
        # Create and display welcome screen
        self.welcome_frame = tk.Frame(self.root, bg="lightblue")
        self.welcome_frame.pack(expand=True, fill="both")

        self.welcome_label = tk.Label(
            self.welcome_frame,
            text="\U0001F5DE\ufe0f Welcome to The News App \U0001F5DE\ufe0f",
            font=("Helvetica", 20, "bold"),
            bg="lightblue"
        )
        self.welcome_label.place(relx=0.5, rely=0.5, anchor="center")

        self.root.after(100, self.fade_in_window)

    def fade_in_window(self):
        # Perform fade-in animation
        if self.fade_alpha < 1.0:
            self.fade_alpha += 0.05
            self.root.attributes("-alpha", self.fade_alpha)
            self.root.after(50, self.fade_in_window)
        else:
            self.root.after(2000, self.fade_out_welcome)

    def fade_out_welcome(self):
        # Perform fade-out animation
        if self.fade_alpha > 0:
            self.fade_alpha -= 0.05
            self.root.attributes("-alpha", self.fade_alpha)
            self.root.after(50, self.fade_out_welcome)
        else:
            self.start_main_app()

    def start_main_app(self):
        # Destroy welcome frame and set up main interface
        self.root.attributes("-alpha", 0.0)
        self.welcome_frame.destroy()

        # Load button images for newspapers
        self.news_images = {
            "The Economic Times": self.load_image("news_images/economic_times.png"),
            "The Hindu": self.load_image("news_images/the_hindu.png"),
            "The Indian Express": self.load_image("news_images/indian_express.png"),
            "Times of India": self.load_image("news_images/times_of_india.png")
        }

        # Create grid container for newspaper buttons
        self.container = ttk.Frame(self.root, padding=20)
        self.container.pack(expand=True, fill="both")

        for i in range(2):
            self.container.columnconfigure(i, weight=1)
            self.container.rowconfigure(i, weight=1)

        # Style for headline buttons (center-aligned)
        self.style.configure("Headline.TButton", anchor="center", font=("Helvetica", 12, "bold"))

        # Add newspaper slots
        self.create_slots()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.fade_alpha = 0.0
        self.root.after(50, self.fade_in_main)

    def fade_in_main(self):
        # Fade-in animation for main screen
        if self.fade_alpha < 1.0:
            self.fade_alpha += 0.05
            self.root.attributes("-alpha", self.fade_alpha)
            self.root.after(50, self.fade_in_main)

    def load_image(self, path):
        # Load and resize image for button
        try:
            img = Image.open(path).resize((400, 400))
            return ImageTk.PhotoImage(img)
        except:
            return None

    def create_slots(self):
        # Create a button for each newspaper
        newspapers = ["The Economic Times", "The Hindu", "The Indian Express", "Times of India"]
        for i, newspaper in enumerate(newspapers):
            self.create_button(newspaper, i)

    def create_button(self, newspaper, index):
        # Create a newspaper button with image and label
        image = self.news_images.get(newspaper)
        button = tk.Button(
            self.container,
            image=image,
            text=newspaper,
            compound="center",
            font=("Helvetica", 12, "bold"),
            fg="white",
            bg="black",
            borderwidth=0,
            highlightthickness=0
        )
        button.config(command=lambda n=newspaper, b=button: self.animate_button(n, b))
        button.grid(row=index // 2, column=index % 2, padx=10, pady=10, ipadx=5, ipady=5, sticky="nsew")

    def animate_button(self, newspaper, button):
        # Provide feedback animation and run scraper first, then open news list
        button.config(bg="gray")
        self.root.after(150, lambda: [
            button.config(bg="black"),
            self.run_scraper_and_open_news(newspaper)
        ])

    def run_scraper_and_open_news(self, newspaper):
        # Map newspaper to corresponding main.py script
        scraper_map = {
            "The Economic Times": "ETmain.py",
            "The Hindu": "THmain.py",
            "The Indian Express": "TIEmain.py",
            "Times of India": "TOImain.py"
        }
    
        script = scraper_map.get(newspaper)
        if not script:
            # fallback: just open news without scraper
            self.open_news_page(newspaper, self.root)
            return
    
        try:
            # Print current working directory and script absolute path for debugging
            cwd = os.path.abspath(".")
            script_path = os.path.abspath(os.path.join("newspapers", script))
            print("Current working directory:", cwd)
            print("Running scraper script:", script_path)
    
            # Run scraper script as a subprocess
            subprocess.run(
                [sys.executable, script_path],
                cwd=cwd,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running {script}: {e}")
            # Optionally show an error dialog here
    
        # After scraper finishes, open the news page
        self.open_news_page(newspaper, self.root)


    def open_news_page(self, newspaper, previous_window):
        previous_window.withdraw()
        news_window = tk.Toplevel(self.root)
        news_window.title(newspaper)

        news_window.protocol("WM_DELETE_WINDOW", lambda: self.back_to_previous(news_window, previous_window))
        news_window.bind("<Escape>", lambda e: self.back_to_previous(news_window, previous_window))
        
        width, height = 800, 600
    
        # Center the window on the screen
        screen_width = news_window.winfo_screenwidth()
        screen_height = news_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        news_window.geometry(f"{width}x{height}+{x}+{y}")
    
        news_window.protocol("WM_DELETE_WINDOW", lambda: self.back_to_previous(news_window, previous_window))
    
        # === Frame to hold canvas and scrollbar ===
        container = ttk.Frame(news_window)
        container.pack(fill="both", expand=True)
    
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    
        # === Frame that will be scrollable ===
        scrollable_frame = ttk.Frame(canvas)
    
        # Update scrollregion when content changes
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
        # Add the scrollable frame inside the canvas
        window_in_canvas = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
        # Make scrollable_frame match canvas width
        def resize_scrollable_frame(event):
            canvas.itemconfig(window_in_canvas, width=event.width)
    
        canvas.bind("<Configure>", resize_scrollable_frame)
    
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # ===== Enable mouse wheel scrolling =====
    
        def _on_mousewheel(event):
            # Windows and MacOS
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
        def _on_mousewheel_linux(event):
            # Linux: Button-4 is scroll up, Button-5 is scroll down
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
    
        # Bind mouse wheel events for scrolling
        canvas.bind_all("<MouseWheel>", _on_mousewheel)       # Windows and Mac
        canvas.bind_all("<Button-4>", _on_mousewheel_linux)   # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel_linux)   # Linux scroll down
    
        # === News Buttons inside scrollable frame ===
        news_list = self.load_headlines_from_json(newspaper)
    
        for headline, _ in news_list:
            news_button = ttk.Button(
            scrollable_frame, text=headline, style="Headline.TButton",
            command=lambda h=headline: self.show_description_from_json(newspaper, h, news_window)
        )

            news_button.pack(fill="x", padx=10, pady=5)
    
        # === Back Button pinned to bottom ===
        back_button = ttk.Button(
            news_window, text="Back",
            command=lambda: self.back_to_previous(news_window, previous_window)
        )
        back_button.pack(side="bottom", fill="x", pady=10)
    

    def load_headlines_from_json(self, newspaper):
        # Map each newspaper to its respective JSON file
        file_map = {
            "The Economic Times": "files/ET/et_stories.json",
            "The Hindu": "files/TH/th_stories.json",
            "The Indian Express": "files/IE/ie_stories.json",
            "Times of India": "files/TOI/toi_stories.json"
        }
        try:
            with open(file_map[newspaper], 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [(item.get("Headline", "No Title"), item.get("Paragraph", "No Description")) for item in data]
        except Exception as e:
            return [("Error loading headlines", str(e))]


    def open_news_description(self, title, description, previous_window, image_url=None, datetime_str="", link=None):
        previous_window.withdraw()

        description_window = tk.Toplevel(self.root)
        description_window.title(title)

        description_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        description_window.bind("<Escape>", lambda e: self.back_to_previous(description_window, previous_window))

        description_window.geometry("1000x800")
        description_window.minsize(400, 300)  # Optional min size

        top_frame = ttk.Frame(description_window, padding=10)
        top_frame.pack(fill="both", expand=True)

        # Frame to hold image and maintain fixed size + 4:3 ratio approximation
        image_frame = ttk.Frame(top_frame)
        image_frame.pack(fill="x", expand=False)

        # Fix frame size and prevent it from resizing to image
        image_frame.config(width=400, height=300)
        image_frame.pack_propagate(False)

        image_label = tk.Label(image_frame)
        image_label.pack(expand=True)

        # Placeholder if no image
        no_image_label = None

        def resize_image(event=None):
            if not image_url or not hasattr(image_label, "original_image"):
                return
        
            frame_width = image_frame.winfo_width()
            frame_height = image_frame.winfo_height()
        
            # Skip resizing if frame not yet properly sized
            if frame_width <= 0 or frame_height <= 0:
                return
        
            orig_width, orig_height = image_label.original_image.size
            ratio = orig_width / orig_height
        
            if frame_width / frame_height > ratio:
                new_height = frame_height
                new_width = int(new_height * ratio)
            else:
                new_width = frame_width
                new_height = int(new_width / ratio)
        
            if new_width <= 0 or new_height <= 0:
                return  # Extra safety check
        
            current_size = getattr(image_label, "current_size", None)
            if current_size == (new_width, new_height):
                return
        
            try:
                resample_method = Image.Resampling.LANCZOS
            except AttributeError:
                resample_method = Image.ANTIALIAS
        
            resized_img = image_label.original_image.resize((new_width, new_height), resample=resample_method)
            photo = ImageTk.PhotoImage(resized_img)
        
            image_label.configure(image=photo)
            image_label.image = photo
            image_label.current_size = (new_width, new_height)
        

        if image_url:
            try:
                local_path = os.path.abspath(image_url)

                if os.path.exists(local_path):
                    # It's a local image path
                    pil_image = Image.open(local_path)
                else:
                    # It's a URL
                    with urllib.request.urlopen(image_url) as u:
                        raw_data = u.read()
                    pil_image = Image.open(io.BytesIO(raw_data))

                image_label.original_image = pil_image

                # Initial resize and bind resizing event once
                resize_image()
                image_frame.bind("<Configure>", resize_image)

            except Exception as e:
                no_image_label = tk.Label(image_frame, text="No image found", font=("Helvetica", 14, "italic"), foreground="gray")
                no_image_label.pack(pady=20)
                print(f"Error loading image: {e}")
        else:
            no_image_label = tk.Label(image_frame, text="No image found", font=("Helvetica", 14, "italic"), foreground="gray")
            no_image_label.pack(pady=20)

        # === Title and Date-Time ===
        title_frame = ttk.Frame(top_frame)
        title_frame.pack(fill="x", pady=(10, 5))

        title_label = ttk.Label(title_frame, text=title, font=("Helvetica", 16, "bold"), anchor="w", wraplength=950, justify="left")
        title_label.pack(side="left", padx=5, fill="x", expand=True)

        datetime_label = ttk.Label(title_frame, text=datetime_str, font=("Helvetica", 10), anchor="e", foreground="gray")
        datetime_label.pack(side="right", padx=5)

        # === Scrollable description ===
        desc_frame = ttk.Frame(top_frame)
        desc_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(desc_frame)
        scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=scrollable, anchor="nw")

        def resize_scrollable(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_scrollable)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === Enable Mouse Wheel Scrolling ===
        def _on_mousewheel(event):
            if sys.platform == 'darwin':
                canvas.yview_scroll(-1 * event.delta, "units")  # macOS
            else:
                canvas.yview_scroll(-1 * (event.delta // 120), "units")  # Windows/Linux

        canvas.bind_all("<MouseWheel>", _on_mousewheel)       # Windows and macOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down

        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

        # === News Description ===
        desc_label = ttk.Label(
            scrollable, text=description, wraplength=700, justify="left"
        )
        desc_label.pack(padx=10, pady=10, anchor="w")

        # === Hyperlink to full article ===
        if link:
            link_frame = ttk.Frame(scrollable)
            link_frame.pack(fill="x", padx=10, pady=(0, 20))
            
            def open_link():
                webbrowser.open(link)
                
            link_btn = ttk.Button(
                link_frame, 
                text="🔗 Read Full Article", 
                command=open_link
            )
            link_btn.pack(pady=5)

        # === Back Button ===
        back_button = ttk.Button(description_window, text="Back", command=lambda: self.back_to_previous(description_window, previous_window))
        back_button.pack(side="bottom", fill="x", pady=10)
    
    def show_description_from_json(self, newspaper, headline, previous_window):
        from_path = {
            "The Economic Times": ("ET", "et_stories.json"),
            "The Hindu": ("TH", "th_stories.json"),
            "The Indian Express": ("IE", "ie_stories.json"),
            "Times of India": ("TOI", "toi_stories.json")
        }
    
        if newspaper not in from_path:
            self.open_news_description("Error", "Newspaper not recognized", previous_window)
            return
    
        subfolder, filename = from_path[newspaper]
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "..", "files", subfolder, filename)
    
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    
            for item in data:
                if item.get("Headline") == headline:
                    index = item.get("Index", None)
    
                    if index is not None:
                        try:
                            if newspaper == "The Economic Times":
                                scrape_single_et_article(index)
                            elif newspaper == "The Hindu":
                                scrape_single_th_article(index)
                            elif newspaper == "The Indian Express":
                                scrape_single_ie_article(index)
                            elif newspaper == "Times of India":
                                scrape_single_toi_article(index)
    
                            # Reload JSON after scrape
                            with open(json_path, 'r', encoding='utf-8') as updated_file:
                                data = json.load(updated_file)
                                item = next((x for x in data if x.get("Index") == index), item)
    
                        except Exception as e:
                            print(f"[ERROR] Failed to refresh {newspaper} article: {e}")
    
                    title = item.get("Headline", "No Title")
                    paragraph = item.get("Paragraph", "No Description")
                    image_url = item.get("Image Path") or item.get("Image URL")
                    datetime_str = item.get("Date and Time", "")
                    link = item.get("News URL")
    
                    self.open_news_description(title, paragraph, previous_window, image_url, datetime_str, link)
                    return
    
            self.open_news_description("Not Found", f"No article found for: {headline}", previous_window)
    
        except Exception as e:
            self.open_news_description("Error", f"Failed to load: {e}", previous_window)


    def back_to_previous(self, current_window, previous_window):
        # Return to previous screen
        current_window.destroy()
        previous_window.deiconify()

    def on_closing(self):
        # Gracefully exit app
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    # Entry point to launch app
    root = tk.Tk()
    root.geometry("800x600")
    app = NewsApp(root)
    root.mainloop()
