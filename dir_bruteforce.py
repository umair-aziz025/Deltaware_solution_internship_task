import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import requests
import threading
from queue import Queue
import sys
from datetime import datetime

# --- Core Scanning Logic (adapted from your script) ---

def test_url(session, url, results_queue):
    """Tests a single URL and puts the result in the queue if found."""
    try:
        response = session.head(url, timeout=3, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 404:
            if response.status_code == 405: # Fallback to GET if HEAD is not allowed
                response = session.get(url, timeout=3, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code != 404:
                result = f"[+] Found: {url} [Status: {response.status_code}]"
                results_queue.put(result)
    except requests.exceptions.RequestException:
        pass

def path_worker(q, stop_event, base_url, extensions, results_queue):
    """Worker thread function."""
    with requests.Session() as session:
        while not q.empty() and not stop_event.is_set():
            path = q.get()
            q.task_done()
            
            # Test path as is
            test_url(session, f"{base_url}/{path}", results_queue)
            
            # Test with extensions
            if extensions and not stop_event.is_set():
                for ext in extensions:
                    if not path.endswith(ext):
                        test_url(session, f"{base_url}/{path}{ext}", results_queue)


# --- GUI Application Class ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Web Path Bruteforcer")
        self.geometry("700x500")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        # State Variables
        self.scan_thread = None
        self.stop_event = threading.Event()
        self.q = Queue()
        self.results_queue = Queue()
        self.total_tasks = 0
        self.completed_tasks = 0

        # Create Widgets
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="Target URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://example.com")
        self.url_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(input_frame, text="Wordlist:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.wordlist_entry = ctk.CTkEntry(input_frame, placeholder_text="Path to your wordlist file")
        self.wordlist_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = ctk.CTkButton(input_frame, text="Browse", width=80, command=self.browse_file)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)
        
        ctk.CTkLabel(input_frame, text="Threads:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.threads_entry = ctk.CTkEntry(input_frame)
        self.threads_entry.insert(0, "50")
        self.threads_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(input_frame, text="Extensions:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.extensions_entry = ctk.CTkEntry(input_frame, placeholder_text=".php, .html (optional)")
        self.extensions_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        control_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.start_button = ctk.CTkButton(control_frame, text="Start Scan", command=self.start_scan)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.stop_button = ctk.CTkButton(control_frame, text="Stop Scan", state="disabled", fg_color="#D32F2F", hover_color="#B71C1C", text_color="#FFFFFF", command=self.stop_scan)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.save_button = ctk.CTkButton(control_frame, text="Save Results", command=self.save_results)
        self.save_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.results_textbox = ctk.CTkTextbox(output_frame, state="disabled", wrap="word", font=("Courier New", 12))
        self.results_textbox.grid(row=0, column=0, sticky="nsew")
        
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode='determinate')
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self, text="Status: Idle")
        self.status_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        self.copyright_label = ctk.CTkLabel(self, text="Copyright \u00A9 Made by Umair", font=("Arial", 11, "italic"), text_color="#999999")
        self.copyright_label.grid(row=5, column=0, padx=10, pady=0, sticky="s")

    def browse_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, filepath)
    
    def log(self, message):
        self.results_textbox.configure(state="normal")
        self.results_textbox.insert(tk.END, message + "\n")
        self.results_textbox.configure(state="disabled")
        self.results_textbox.see(tk.END)
        
    def start_scan(self):
        # Reset UI and state variables
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", tk.END)
        self.results_textbox.configure(state="disabled")
        self.progress_bar.set(0)
        self.stop_event.clear()
        self.q = Queue()
        self.results_queue = Queue()
        self.completed_tasks = 0

        # Get inputs and validate
        base_url = self.url_entry.get().rstrip('/')
        wordlist_path = self.wordlist_entry.get()
        if not base_url or not wordlist_path:
            self.log("[-] Error: URL and Wordlist are required.")
            return

        try:
            with open(wordlist_path, "r", errors='ignore') as f:
                wordlist = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                for path in wordlist:
                    self.q.put(path)
        except FileNotFoundError:
            self.log(f"[-] Error: Wordlist file not found at '{wordlist_path}'.")
            return
            
        self.total_tasks = self.q.qsize()
        if self.total_tasks == 0:
            self.log("[-] Error: Wordlist is empty or only contains comments.")
            return
            
        self.log("-" * 50)
        self.log(f"Target: {base_url}")
        self.log(f"Wordlist contains {self.total_tasks} paths.")
        self.log(f"Time Started: {datetime.now()}")
        self.log("-" * 50)
        
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="enabled", cursor="hand2")
        self.status_label.configure(text="Status: Scanning...")

        # Start the worker threads
        num_threads = int(self.threads_entry.get())
        extensions_str = self.extensions_entry.get()
        extensions = [ext.strip() for ext in extensions_str.split(',') if ext.strip()] if extensions_str else []
        
        for _ in range(num_threads):
            threading.Thread(target=path_worker, args=(self.q, self.stop_event, base_url, extensions, self.results_queue), daemon=True).start()

        # Start the non-blocking GUI update loop
        self.update_gui()

    def update_gui(self):
        """Periodically checks queues and updates the GUI. This is the non-blocking part."""
        # Process any found results
        while not self.results_queue.empty():
            self.log(self.results_queue.get())
        
        # Update progress
        self.completed_tasks = self.total_tasks - self.q.qsize()
        progress = self.completed_tasks / self.total_tasks
        self.progress_bar.set(progress)

        # Check if the scan should continue
        if self.q.empty() or self.stop_event.is_set():
            self.scan_finished()
        else:
            # Reschedule itself to run again
            self.after(100, self.update_gui)

    def scan_finished(self):
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled", cursor="arrow")
        if self.stop_event.is_set():
            self.status_label.configure(text=f"Status: Stopped by user at {self.completed_tasks}/{self.total_tasks} paths.")
            self.log("\n--- Scan Stopped By User ---")
        else:
            self.status_label.configure(text="Status: Scan Complete!")
            self.log("\n--- Scan Complete ---")
            self.progress_bar.set(1.0) # Ensure it shows 100%

    def stop_scan(self):
        """Signals the scanning threads to stop."""
        self.stop_event.set()
    
    def save_results(self):
        content = self.results_textbox.get("1.0", tk.END)
        if not content.strip():
            self.log("[-] Info: Nothing to save.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Results As"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"[+] Results saved to {filepath}")

if __name__ == "__main__":
    app = App()
    app.mainloop()