import tkinter as tk
from GUI.gui import NewsApp

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = NewsApp(root)
    root.mainloop()
