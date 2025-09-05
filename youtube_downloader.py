#!/usr/bin/env python3
"""
Ultra-Robust YouTube Video Downloader
A GUI application that handles YouTube's format restrictions and signature issues
"""

# Auto-setup environment when app starts
try:
    from pathlib import Path
    import subprocess
    import sys
    import os
    
    # Check if this is the first run (no venv or FFmpeg)
    project_root = Path(__file__).parent
    needs_setup = False
    
    # Check if venv exists and has packages
    venv_path = project_root / "venv"
    if not venv_path.exists():
        needs_setup = True
    else:
        # Check if yt-dlp is installed in venv
        try:
            if sys.platform == "win32":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            
            if not pip_path.exists():
                needs_setup = True
            else:
                # Quick check if main dependencies are installed
                result = subprocess.run([str(pip_path), "show", "yt-dlp"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    needs_setup = True
        except:
            needs_setup = True
    
    # Check if FFmpeg exists
    ffmpeg_paths = [
        project_root / "venv" / "ffmpeg" / "ffmpeg.exe",  # setup.py location
        project_root / "ffmpeg_bin" / "ffmpeg.exe",      # old auto-install location
    ]
    
    ffmpeg_exists = any(p.exists() for p in ffmpeg_paths)
    if not ffmpeg_exists:
        # Check system FFmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=3)
            ffmpeg_exists = True
        except:
            needs_setup = True
    
    # Run setup if needed
    if needs_setup:
        print("🚀 First run detected - setting up environment...")
        print("This may take a few minutes to download FFmpeg and dependencies.\n")
        
        # Import and run setup
        import setup
        setup.main()
        
        print("\n✅ Setup complete! Starting application...\n")
except Exception as e:
    print(f"⚠️ Setup check failed: {e}")
    print("Continuing with manual setup...\n")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import re
import subprocess
from pathlib import Path
import yt_dlp
from datetime import datetime
import webbrowser
from tkinter import font as tkFont

class YouTubeDownloader:
    def __init__(self):
        # Setup local FFmpeg path if available
        self._setup_local_ffmpeg()
        
        self.root = tk.Tk()
        self.root.title("🎥 YouTube Downloader Pro")
        self.root.geometry("1000x900")
        self.root.minsize(900, 750)
        
        # Modern color scheme
        self.colors = {
            'bg': '#f0f2f5',           # Light gray background
            'card_bg': '#ffffff',       # White card background
            'primary': '#1976d2',       # Blue primary
            'primary_dark': '#1565c0',  # Darker blue
            'success': '#4caf50',       # Green
            'warning': '#ff9800',       # Orange
            'error': '#f44336',         # Red
            'text': '#212529',          # Dark text
            'text_secondary': '#6c757d', # Gray text
            'border': '#dee2e6',        # Light border
            'accent': '#e3f2fd'         # Light blue accent
        }
        
        self.setup_theme()
        
        # Initialize tooltips list early
        self.tooltips = []
        
        # Variables - Set default download path to project directory
        project_downloads = Path(__file__).parent / "downloads"
        project_downloads.mkdir(exist_ok=True)  # Create downloads folder if it doesn't exist
        self.download_path = tk.StringVar(value=str(project_downloads))
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="720p")
        self.format_var = tk.StringVar(value="any")
        self.subtitle_var = tk.BooleanVar(value=False)
        self.playlist_var = tk.BooleanVar(value=False)  # Start with single video mode (unchecked)
        self.playlist_start_var = tk.StringVar(value="1")
        self.playlist_end_var = tk.StringVar(value="")
        
        # Download system
        self.is_downloading = False
        self.current_playlist_info = None  # Store current playlist info
        self.selected_playlist_indices = []  # Store individually selected playlist videos
        
        # Settings file
        self.settings_file = Path("settings.json")
        
        self.setup_tooltips()
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        self.reset_all_options()  # Reset all options on app startup
        self.load_settings()
        
    def setup_theme(self):
        """Configure modern theme and styling"""
        # Set background color
        self.root.configure(bg=self.colors['bg'])
        
        # Create custom fonts
        try:
            self.fonts = {
                'title': tkFont.Font(family="Segoe UI", size=18, weight="bold"),
                'heading': tkFont.Font(family="Segoe UI", size=12, weight="bold"),
                'body': tkFont.Font(family="Segoe UI", size=10),
                'small': tkFont.Font(family="Segoe UI", size=9)
            }
        except:
            # Fallback fonts if Segoe UI is not available
            self.fonts = {
                'title': tkFont.Font(family="Arial", size=18, weight="bold"),
                'heading': tkFont.Font(family="Arial", size=12, weight="bold"),
                'body': tkFont.Font(family="Arial", size=10),
                'small': tkFont.Font(family="Arial", size=9)
            }
        
        # Configure ttk styles
        style = ttk.Style()
        
        # Configure button styles with better visibility
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=2,
                       relief='raised',
                       focuscolor='none',
                       font=self.fonts['body'])
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark']),
                           ('pressed', self.colors['primary_dark'])],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'raised')])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=2,
                       relief='raised',
                       focuscolor='none',
                       font=self.fonts['body'])
        
        style.map('Success.TButton',
                 background=[('active', '#388e3c'),
                           ('pressed', '#2e7d32')],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'raised')])
        
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='white',
                       borderwidth=2,
                       relief='raised',
                       focuscolor='none',
                       font=self.fonts['body'])
        
        style.map('Warning.TButton',
                 background=[('active', '#f57c00'),
                           ('pressed', '#e65100')],
                 foreground=[('active', 'white'),
                           ('pressed', 'white')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'raised')])
        
        # Configure regular button style with proper colors
        style.configure('TButton',
                       background='#e0e0e0',
                       foreground='black',
                       borderwidth=2,
                       relief='raised',
                       focuscolor='none',
                       font=self.fonts['body'])
        
        style.map('TButton',
                 background=[('active', '#d0d0d0'),
                           ('pressed', '#c0c0c0')],
                 foreground=[('active', 'black'),
                           ('pressed', 'black')],
                 relief=[('pressed', 'sunken'),
                        ('active', 'raised')])
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       background=self.colors['card_bg'],
                       relief='flat',
                       borderwidth=1)
        
        # Configure label frame styles
        style.configure('Card.TLabelframe',
                       background=self.colors['card_bg'],
                       borderwidth=1,
                       relief='solid',
                       labelmargins=[10, 5, 10, 5])
        
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['card_bg'],
                       font=self.fonts['heading'],
                       foreground=self.colors['primary'])
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better accessibility"""
        # URL entry shortcuts
        self.root.bind('<Control-v>', lambda e: self.paste_url())
        self.root.bind('<Control-V>', lambda e: self.paste_url())
        
        # Function key shortcuts
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.analyze_url() if self.url_var.get().strip() else None)
        self.root.bind('<F9>', lambda e: self.start_download() if not self.is_downloading else None)
        self.root.bind('<F10>', lambda e: self.stop_download() if self.is_downloading else None)
        self.root.bind('<F12>', lambda e: self.clear_log())
        
        # Alt shortcuts
        self.root.bind('<Alt-o>', lambda e: self.open_download_folder())
        self.root.bind('<Alt-O>', lambda e: self.open_download_folder())
        self.root.bind('<Alt-b>', lambda e: self.browse_folder())
        self.root.bind('<Alt-B>', lambda e: self.browse_folder())
        
        # Ctrl shortcuts
        self.root.bind('<Control-l>', lambda e: self.clear_log())
        self.root.bind('<Control-L>', lambda e: self.clear_log())
        self.root.bind('<Control-t>', lambda e: self.test_formats())
        self.root.bind('<Control-T>', lambda e: self.test_formats())
        self.root.bind('<Control-r>', lambda e: self.manual_reset_options())
        self.root.bind('<Control-R>', lambda e: self.manual_reset_options())
        
        # Enter key in URL field
        self.url_entry.bind('<Return>', lambda e: self.analyze_url())
        
        # Escape key to stop download
        self.root.bind('<Escape>', lambda e: self.stop_download() if self.is_downloading else None)
        
    def setup_tooltips(self):
        """Setup tooltips for better user experience"""
        # Create a simple tooltip class
        class ToolTip:
            def __init__(self, widget, text):
                self.widget = widget
                self.text = text
                self.widget.bind('<Enter>', self.on_enter)
                self.widget.bind('<Leave>', self.on_leave)
                self.tooltip_window = None
            
            def on_enter(self, event=None):
                x, y, _, _ = self.widget.bbox('insert') if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
                x += self.widget.winfo_rootx() + 25
                y += self.widget.winfo_rooty() + 25
                
                self.tooltip_window = tw = tk.Toplevel(self.widget)
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f'+{x}+{y}')
                
                label = tk.Label(tw, text=self.text, justify='left',
                               background='#333333', foreground='white',
                               relief='solid', borderwidth=1,
                               font=('Arial', 9, 'normal'), padx=8, pady=4)
                label.pack()
            
            def on_leave(self, event=None):
                if self.tooltip_window:
                    self.tooltip_window.destroy()
                    self.tooltip_window = None
        
        # Store ToolTip class for later use
        self.ToolTip = ToolTip
        
    def show_help(self):
        """Show help dialog with keyboard shortcuts"""
        help_text = """YouTube Downloader Pro - Keyboard Shortcuts
        
🔤 General Shortcuts:
F1 - Show this help
F5 - Analyze URL
F9 - Start download
F10 - Stop download
F12 - Clear log
Esc - Stop download

📋 Clipboard & Files:
Ctrl+V - Paste URL from clipboard
Alt+B - Browse for download folder
Alt+O - Open download folder

🔧 Tools:
Ctrl+L - Clear log
Ctrl+T - Test formats
Ctrl+R - Reset all options
Enter (in URL field) - Analyze URL

💡 Tips:
• Valid YouTube URLs are automatically detected
• Progress is shown with colored status indicators
• Download logs are color-coded by importance
• Playlist range can be customized"""
        
        messagebox.showinfo("Help - Keyboard Shortcuts", help_text)
        
    def setup_mouse_wheel_scrolling(self):
        """Setup mouse wheel scrolling for the canvas"""
        def on_mouse_wheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        
        def unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        # Bind mouse wheel events
        self.canvas.bind('<Enter>', bind_to_mousewheel)
        self.canvas.bind('<Leave>', unbind_from_mousewheel)
        
    def setup_ui(self):
        """Set up the user interface with scrollable content"""
        # Create a canvas and scrollbar for scrolling
        canvas = tk.Canvas(self.root, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        # Create scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize to update scrollable frame width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create main content frame inside scrollable frame
        main_frame = ttk.Frame(scrollable_frame, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        
        # Store canvas reference for mouse wheel scrolling
        self.canvas = canvas
        self.setup_mouse_wheel_scrolling()
        
        # Title with emoji and modern styling
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        title_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(title_frame, text="🎥 YouTube Downloader Pro", 
                               font=self.fonts['title'], foreground=self.colors['primary'])
        title_label.grid(row=0, column=0)
        
        subtitle_label = ttk.Label(title_frame, text="Download YouTube videos and playlists with ease", 
                                 font=self.fonts['body'], foreground=self.colors['text_secondary'])
        subtitle_label.grid(row=1, column=0, pady=(5, 0))
        
        # URL input section with modern styling
        url_frame = ttk.LabelFrame(main_frame, text="🔗 Video/Playlist URL", padding="10")
        url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        url_frame.columnconfigure(1, weight=1)
        
        # URL input with placeholder-like hint
        url_input_frame = ttk.Frame(url_frame)
        url_input_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_input_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.url_var, 
                                 font=self.fonts['body'])
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # URL validation indicator
        self.url_status_label = ttk.Label(url_input_frame, text="", font=self.fonts['small'])
        self.url_status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Bind URL validation
        self.url_var.trace('w', self.validate_url_realtime)
        
        # Analyze button with icon and high contrast
        self.analyze_btn = tk.Button(url_input_frame, text="🔍 Analyze", 
                                   command=self.analyze_url,
                                   bg=self.colors['primary'], fg='white',
                                   font=self.fonts['body'], relief='raised',
                                   borderwidth=2, padx=15, pady=5)
        self.analyze_btn.grid(row=0, column=1)
        
        # Quick paste button
        self.paste_btn = tk.Button(url_input_frame, text="📋 Paste", 
                                 command=self.paste_url,
                                 bg='#e0e0e0', fg='black',
                                 font=self.fonts['body'], relief='raised',
                                 borderwidth=2, padx=10, pady=5)
        self.paste_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Add tooltips to URL section
        self.tooltips.append(self.ToolTip(self.url_entry, "Enter or paste a YouTube video or playlist URL\n(Press Enter to analyze)"))
        self.tooltips.append(self.ToolTip(self.analyze_btn, "Analyze the YouTube URL to get video information\n(Shortcut: F5)"))
        self.tooltips.append(self.ToolTip(self.paste_btn, "Paste URL from clipboard\n(Shortcut: Ctrl+V)"))
        
        # Hint text
        hint_label = ttk.Label(url_frame, 
                             text="Paste a YouTube video or playlist URL above", 
                             font=self.fonts['small'], foreground=self.colors['text_secondary'])
        hint_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 0))
        
        # Video info section with modern styling
        info_frame = ttk.LabelFrame(main_frame, text="📊 Video Information", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=5, width=70, 
                                                  state=tk.DISABLED, wrap=tk.WORD,
                                                  bg=self.colors['accent'],
                                                  font=self.fonts['body'],
                                                  relief='flat', borderwidth=1)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Download options section with modern grid layout
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Download Options", padding="10")
        options_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)
        
        # Quality selection with icon
        ttk.Label(options_frame, text="🎥 Quality:", font=self.fonts['body']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(0, 10))
        self.quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, 
                                        values=["Best Quality", "720p", "480p", "360p", "240p", "Data Saving", "Audio Only"],
                                        font=self.fonts['body'], width=15)
        self.quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 30), pady=(0, 10))
        
        # Format selection with icon
        ttk.Label(options_frame, text="📁 Format:", font=self.fonts['body']).grid(
            row=0, column=2, sticky=tk.W, padx=(0, 10), pady=(0, 10))
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var,
                                  values=["any", "mp4", "webm"],
                                  font=self.fonts['body'], width=10)
        format_combo.grid(row=0, column=3, sticky=tk.W, pady=(0, 10))
        
        # Separator
        separator = ttk.Separator(options_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 15))
        
        # Checkboxes with icons and better styling
        checkbox_frame = ttk.Frame(options_frame)
        checkbox_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        ttk.Checkbutton(checkbox_frame, text="📝 Download subtitles", 
                       variable=self.subtitle_var, style='TCheckbutton').pack(
                           side=tk.LEFT, padx=(0, 30))
        ttk.Checkbutton(checkbox_frame, text="📜 Download entire playlist", 
                       variable=self.playlist_var, command=self.toggle_playlist_range,
                       style='TCheckbutton').pack(side=tk.LEFT)
        
        # Playlist range selection (initially hidden) - moved to separate frame
        self.playlist_range_frame = ttk.Frame(options_frame)
        self.playlist_range_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Playlist range controls with modern styling
        range_label = ttk.Label(self.playlist_range_frame, text="🎯 Playlist Range:", 
                              font=self.fonts['body'], foreground=self.colors['primary'])
        range_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(self.playlist_range_frame, text="From:", font=self.fonts['body']).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.start_entry = ttk.Entry(self.playlist_range_frame, textvariable=self.playlist_start_var, 
                                   width=6, font=self.fonts['body'])
        self.start_entry.grid(row=0, column=2, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(self.playlist_range_frame, text="To:", font=self.fonts['body']).grid(
            row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.end_entry = ttk.Entry(self.playlist_range_frame, textvariable=self.playlist_end_var, 
                                 width=6, font=self.fonts['body'])
        self.end_entry.grid(row=0, column=4, sticky=tk.W, padx=(0, 15))
        
        # Show playlist button with icon
        self.show_playlist_btn = tk.Button(self.playlist_range_frame, text="📋 Show Playlist", 
                                         command=self.show_playlist_selector, state=tk.DISABLED,
                                         bg=self.colors['primary'], fg='white',
                                         font=self.fonts['body'], relief='raised',
                                         borderwidth=2, padx=10, pady=5)
        self.show_playlist_btn.grid(row=0, column=5, sticky=tk.W, padx=(0, 10))
        
        # Hint text for playlist range
        hint_label = ttk.Label(self.playlist_range_frame, 
                             text="Leave 'To' empty to download all remaining videos", 
                             font=self.fonts['small'], foreground=self.colors['text_secondary'])
        hint_label.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(5, 0))
        
        # Initially hide the playlist range frame
        self.playlist_range_frame.grid_remove()
        
        # Destination section with modern styling
        dest_frame = ttk.LabelFrame(main_frame, text="📁 Download Destination", padding="10")
        dest_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        dest_frame.columnconfigure(1, weight=1)
        
        # Path selection with better styling
        path_frame = ttk.Frame(dest_frame)
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        path_frame.columnconfigure(0, weight=1)
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.download_path, 
                                  font=self.fonts['body'])
        self.path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.browse_btn = tk.Button(path_frame, text="📂 Browse", 
                                  command=self.browse_folder,
                                  bg='#e0e0e0', fg='black',
                                  font=self.fonts['body'], relief='raised',
                                  borderwidth=2, padx=10, pady=5)
        self.browse_btn.grid(row=0, column=1)
        
        self.open_folder_btn = tk.Button(path_frame, text="📂 Open", 
                                       command=self.open_download_folder,
                                       bg='#e0e0e0', fg='black',
                                       font=self.fonts['body'], relief='raised',
                                       borderwidth=2, padx=10, pady=5)
        self.open_folder_btn.grid(row=0, column=2, padx=(5, 0))
        # Initially hide the open button
        self.open_folder_btn.grid_remove()
        
        # Add tooltips to destination section
        self.tooltips.append(self.ToolTip(self.path_entry, "Path where downloaded files will be saved"))
        self.tooltips.append(self.ToolTip(self.browse_btn, "Browse for download folder\n(Shortcut: Alt+B)"))
        self.tooltips.append(self.ToolTip(self.open_folder_btn, "Open download folder in file explorer\n(Appears after successful download)\n(Shortcut: Alt+O)"))
        
        # Show current path info
        path_info = ttk.Label(dest_frame, text="Downloads will be saved to the above folder", 
                            font=self.fonts['small'], foreground=self.colors['text_secondary'])
        path_info.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        # Progress section with modern styling
        progress_frame = ttk.LabelFrame(main_frame, text="📋 Download Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400, style='TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status with icon indicator
        status_frame = ttk.Frame(progress_frame)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.status_icon = ttk.Label(status_frame, text="⏸️", font=self.fonts['body'])
        self.status_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready to download", 
                                    font=self.fonts['body'], foreground=self.colors['text'])
        self.status_label.pack(side=tk.LEFT)
        
        # Download log with modern styling
        log_frame = ttk.LabelFrame(main_frame, text="📄 Download Log", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, width=70, wrap=tk.WORD,
                                                bg=self.colors['accent'],
                                                font=self.fonts['small'],
                                                relief='flat', borderwidth=1)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons with modern styling and icons
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=7, column=0, pady=(15, 15))
        
        # Main action buttons
        main_buttons = ttk.Frame(button_frame)
        main_buttons.pack(side=tk.LEFT)
        
        self.download_btn = tk.Button(main_buttons, text="▶️ Download", 
                                    command=self.start_download,
                                    bg=self.colors['success'], fg='white',
                                    font=self.fonts['body'], relief='raised',
                                    borderwidth=2, padx=15, pady=5)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(main_buttons, text="⏹️ Stop", 
                                command=self.stop_download, state=tk.DISABLED,
                                bg=self.colors['error'], fg='white',
                                font=self.fonts['body'], relief='raised',
                                borderwidth=2, padx=15, pady=5)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Utility buttons
        utility_buttons = ttk.Frame(button_frame)
        utility_buttons.pack(side=tk.LEFT)
        
        self.clear_btn = tk.Button(utility_buttons, text="🗑️ Clear Log", 
                                 command=self.clear_log,
                                 bg='#e0e0e0', fg='black',
                                 font=self.fonts['body'], relief='raised',
                                 borderwidth=2, padx=10, pady=5)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_btn = tk.Button(utility_buttons, text="🔍 Test Formats", 
                                command=self.test_formats,
                                bg='#e0e0e0', fg='black',
                                font=self.fonts['body'], relief='raised',
                                borderwidth=2, padx=10, pady=5)
        self.test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_btn = tk.Button(utility_buttons, text="🔄 Reset", 
                                 command=self.manual_reset_options,
                                 bg='#ff9800', fg='white',
                                 font=self.fonts['body'], relief='raised',
                                 borderwidth=2, padx=10, pady=5)
        self.reset_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.help_btn = tk.Button(utility_buttons, text="❓ Help", 
                                command=self.show_help,
                                bg='#e0e0e0', fg='black',
                                font=self.fonts['body'], relief='raised',
                                borderwidth=2, padx=10, pady=5)
        self.help_btn.pack(side=tk.LEFT)
        
        # Add tooltips to control buttons
        self.tooltips.append(self.ToolTip(self.download_btn, "Start downloading the video/playlist\n(Shortcut: F9)"))
        self.tooltips.append(self.ToolTip(self.stop_btn, "Stop the current download\n(Shortcut: F10 or Esc)"))
        self.tooltips.append(self.ToolTip(self.clear_btn, "Clear the download log\n(Shortcut: F12 or Ctrl+L)"))
        self.tooltips.append(self.ToolTip(self.test_btn, "Test available video formats\n(Shortcut: Ctrl+T)"))
        self.tooltips.append(self.ToolTip(self.reset_btn, "Reset all options to defaults\n(Shortcut: Ctrl+R)"))
        self.tooltips.append(self.ToolTip(self.help_btn, "Show keyboard shortcuts and help\n(Shortcut: F1)"))
        
        # Force canvas to update scroll region after UI is created
        self.root.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def validate_url_realtime(self, *args):
        """Real-time URL validation"""
        url = self.url_var.get().strip()
        if not url:
            self.url_status_label.config(text="", foreground=self.colors['text_secondary'])
            return
            
        if self.is_valid_youtube_url(url):
            self.url_status_label.config(text="✓ Valid YouTube URL", 
                                       foreground=self.colors['success'])
        else:
            self.url_status_label.config(text="⚠ Invalid URL - Please enter a valid YouTube URL", 
                                       foreground=self.colors['error'])
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
            self.log_message("📋 Pasted URL from clipboard")
        except tk.TclError:
            messagebox.showwarning("Warning", "No text found in clipboard")
    
    def log_message(self, message, level="info"):
        """Add a message to the log with timestamp and color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Configure text tags for different log levels
        self.log_text.tag_config('info', foreground=self.colors['text'])
        self.log_text.tag_config('success', foreground=self.colors['success'], font=self.fonts['body'])
        self.log_text.tag_config('warning', foreground=self.colors['warning'], font=self.fonts['body'])
        self.log_text.tag_config('error', foreground=self.colors['error'], font=self.fonts['body'])
        self.log_text.tag_config('timestamp', foreground=self.colors['text_secondary'], font=self.fonts['small'])
        
        # Determine log level from message content if not specified
        if level == "info":
            if any(indicator in message for indicator in ['✓', '✅', '🎉', 'completed', 'success']):
                level = "success"
            elif any(indicator in message for indicator in ['⚠', '🚨', 'warning', 'failed']):
                level = "warning"
            elif any(indicator in message for indicator in ['❌', '❗', 'error', 'Error']):
                level = "error"
        
        # Insert timestamp
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Insert message with appropriate color
        self.log_text.insert(tk.END, f"{message}\n", level)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the download log"""
        self.log_text.delete(1.0, tk.END)
        
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            self.save_settings()
    
    def open_download_folder(self):
        """Open the download folder in file explorer"""
        try:
            path = Path(self.download_path.get())
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            
            import os
            if os.name == 'nt':  # Windows
                os.startfile(str(path))
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open' if 'darwin' in os.uname().sysname.lower() else 'xdg-open', str(path)])
            
            self.log_message(f"📂 Opened download folder: {path}")
        except Exception as e:
            self.log_message(f"Could not open folder: {str(e)}")
            messagebox.showerror("Error", f"Could not open download folder:\n{str(e)}")
            
    def toggle_playlist_range(self):
        """Toggle playlist range selection visibility"""
        if self.playlist_var.get():
            self.playlist_range_frame.grid()
            # If we have playlist info, enable the show playlist button
            if self.current_playlist_info and 'entries' in self.current_playlist_info:
                self.show_playlist_btn.config(state=tk.NORMAL)
        else:
            self.playlist_range_frame.grid_remove()
            
    def show_playlist_selector(self):
        """Show playlist video selection dialog"""
        if not self.current_playlist_info or 'entries' not in self.current_playlist_info:
            messagebox.showwarning("Warning", "Please analyze a playlist URL first")
            return
            
        self.open_playlist_selector_window()
        
    def open_playlist_selector_window(self):
        """Open enhanced playlist selector window with modern styling"""
        playlist_window = tk.Toplevel(self.root)
        playlist_window.title("🎥 Playlist Video Selector")
        playlist_window.geometry("1000x750")  # Increased height to show buttons
        # Removed transient and grab_set to allow standard Windows title bar buttons
        playlist_window.configure(bg=self.colors['bg'])
        
        # Enable resizing and all title bar buttons (minimize, maximize, close)
        playlist_window.resizable(True, True)
        playlist_window.minsize(800, 600)  # Set minimum size
        
        # Set window icon and make it stay on top initially
        playlist_window.focus_force()
        playlist_window.lift()
        
        # Center the window
        playlist_window.geometry("+{}+{}".format(
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Main frame with modern styling
        main_frame = ttk.Frame(playlist_window, style='Card.TFrame', padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section with playlist info
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        
        # Playlist title
        playlist_title = self.current_playlist_info.get('title', 'Unknown Playlist')
        title_label = ttk.Label(header_frame, text=f"🎥 {playlist_title}", 
                               font=self.fonts['title'], foreground=self.colors['primary'])
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Playlist stats
        entries = self.current_playlist_info['entries']
        valid_entries = [e for e in entries if e]
        stats_text = f"{len(valid_entries)} videos • Channel: {self.current_playlist_info.get('uploader', 'Unknown')}"
        stats_label = ttk.Label(header_frame, text=stats_text, 
                              font=self.fonts['body'], foreground=self.colors['text_secondary'])
        stats_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Search frame with modern styling
        search_frame = ttk.LabelFrame(main_frame, text="🔎 Search Videos", 
                                    style='Card.TLabelframe', padding="15")
        search_frame.pack(fill=tk.X, pady=(0, 20))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Filter:", font=self.fonts['body']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, 
                               font=self.fonts['body'], width=40)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        clear_search_btn = ttk.Button(search_frame, text="✖ Clear", 
                                    command=lambda: self.search_var.set(""),
                                    style='TButton')
        clear_search_btn.grid(row=0, column=2)
        
        # Hint for search
        search_hint = ttk.Label(search_frame, 
                              text="Type to filter videos by title or uploader", 
                              font=self.fonts['small'], foreground=self.colors['text_secondary'])
        search_hint.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # Selection controls frame
        selection_controls_frame = ttk.LabelFrame(main_frame, text="✅ Selection Controls", 
                                               style='Card.TLabelframe', padding="15")
        selection_controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create frame for selection buttons
        controls_top = ttk.Frame(selection_controls_frame)
        controls_top.pack(fill=tk.X, pady=(0, 10))
        
        # All/None selection buttons with improved styling
        select_all_btn = tk.Button(controls_top, text="✅ Select All", 
                                 command=lambda: select_all_videos(True),
                                 bg="#28a745", fg="white", font=self.fonts['body'],
                                 relief="flat", padx=12, pady=6)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        select_none_btn = tk.Button(controls_top, text="❌ Select None", 
                                  command=lambda: select_all_videos(False),
                                  bg="#dc3545", fg="white", font=self.fonts['body'],
                                  relief="flat", padx=12, pady=6)
        select_none_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        invert_btn = tk.Button(controls_top, text="🔄 Invert Selection", 
                             command=lambda: invert_selection(),
                             bg="#6c757d", fg="white", font=self.fonts['body'],
                             relief="flat", padx=12, pady=6)
        invert_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Range selection
        ttk.Label(controls_top, text="Range:", font=self.fonts['body']).pack(side=tk.LEFT, padx=(0, 5))
        
        range_start = tk.StringVar(value="1")
        range_start_entry = ttk.Entry(controls_top, textvariable=range_start, width=6, font=self.fonts['body'])
        range_start_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(controls_top, text="to", font=self.fonts['body']).pack(side=tk.LEFT, padx=(0, 5))
        
        range_end = tk.StringVar()
        range_end_entry = ttk.Entry(controls_top, textvariable=range_end, width=6, font=self.fonts['body'])
        range_end_entry.pack(side=tk.LEFT, padx=(0, 8))
        
        range_btn = tk.Button(controls_top, text="🎯 Select Range", 
                             command=lambda: select_range(),
                             bg="#007bff", fg="white", font=self.fonts['body'],
                             relief="flat", padx=12, pady=6)
        range_btn.pack(side=tk.LEFT)
        
        # Selection status
        selection_status = ttk.Label(selection_controls_frame, text="0 videos selected", 
                                   font=self.fonts['body'], foreground=self.colors['primary'])
        selection_status.pack(anchor=tk.W)
        
        # ACTION BUTTONS FIRST - Pack buttons before video list to ensure they're visible
        # Separator before action buttons
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(10, 5), side=tk.BOTTOM)
        
        # Action buttons frame (pack at bottom FIRST)
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'], relief='raised', bd=1)
        button_frame.pack(fill=tk.X, pady=(5, 10), side=tk.BOTTOM)
        
        # Create the action buttons immediately
        action_frame = tk.Frame(button_frame, bg=self.colors['bg'])
        action_frame.pack(side=tk.RIGHT, padx=10)
        
        # Note: Commands will be set after functions are defined
        download_btn = tk.Button(action_frame, text="🚀 Download Selected",
                               bg="#28a745", fg="white", font=self.fonts['body'],
                               relief="flat", padx=15, pady=8)
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(action_frame, text="❌ Cancel",
                             command=playlist_window.destroy,
                             bg="#6c757d", fg="white", font=self.fonts['body'],
                             relief="flat", padx=15, pady=8)
        cancel_btn.pack(side=tk.LEFT)
        
        # Info frame on the left
        info_frame = tk.Frame(button_frame, bg=self.colors['bg'])
        info_frame.pack(side=tk.LEFT, padx=10)
        
        # Video list frame with checkboxes (pack after buttons)
        list_frame = ttk.LabelFrame(main_frame, text="📜 Video List (Check videos to download)", 
                                  style='Card.TLabelframe', padding="15")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Create scrollable frame for video checkboxes
        canvas = tk.Canvas(list_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        # Configure canvas window
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make sure the scrollable frame fills the canvas width
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:  # Only if canvas is initialized
                canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_scroll_region)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mouse wheel scrolling support
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind mouse wheel to canvas and all child widgets
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        bind_mousewheel(canvas)
        
        # Store all entries and their check variables
        all_entries = [(i, entry) for i, entry in enumerate([e for e in entries if e], 1)]
        video_checkboxes = []  # List of (checkbox_var, checkbox_widget, entry_data) tuples
        filtered_checkboxes = []  # Currently visible checkboxes after filtering
        
        # Now add the info label after all_entries is defined
        info_text = f"Select videos to download from {len(all_entries)} available"
        info_label = tk.Label(info_frame, text=info_text, 
                            font=self.fonts['small'], fg=self.colors['text_secondary'], bg=self.colors['bg'])
        info_label.pack()
        
        def update_selection_status():
            """Update the selection status label"""
            selected_count = sum(1 for var, _, _ in video_checkboxes if var.get())
            total_visible = len(filtered_checkboxes)
            total_count = len(all_entries)
            
            if total_visible != total_count:
                selection_status.config(text=f"{selected_count} videos selected (from {total_visible}/{total_count} visible)")
            else:
                selection_status.config(text=f"{selected_count} of {total_count} videos selected")
        
        def select_all_videos(select):
            """Select or deselect all visible videos"""
            for var, _, _ in filtered_checkboxes:
                var.set(select)
            update_selection_status()
        
        def invert_selection():
            """Invert the selection of all visible videos"""
            for var, _, _ in filtered_checkboxes:
                var.set(not var.get())
            update_selection_status()
        
        def select_range():
            """Select a range of videos based on the input fields"""
            try:
                start = int(range_start.get())
                end_text = range_end.get().strip()
                end = int(end_text) if end_text else len(all_entries)
                
                if start < 1 or start > len(all_entries):
                    messagebox.showerror("Invalid Range", f"Start must be between 1 and {len(all_entries)}")
                    return
                
                if end < start or end > len(all_entries):
                    messagebox.showerror("Invalid Range", f"End must be between {start} and {len(all_entries)}")
                    return
                
                # First, deselect all videos
                for var, _, entry_data in video_checkboxes:
                    var.set(False)
                
                # Then select videos in the specified range
                for var, _, entry_data in video_checkboxes:
                    video_index = entry_data[0]  # The original index
                    if start <= video_index <= end:
                        var.set(True)
                
                update_selection_status()
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for the range")
        
        def populate_video_list(filter_text=""):
            """Populate video list with checkboxes and optional filtering"""
            # Clear existing checkboxes from the scrollable frame
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            # Clear the filtered list
            filtered_checkboxes.clear()
            
            # Debug: Log entry count
            print(f"DEBUG: Processing {len(all_entries)} entries")
            
            # If this is the first population, create all checkbox variables
            if not video_checkboxes:
                for i, entry in all_entries:
                    if entry:  # Make sure entry is not None
                        checkbox_var = tk.BooleanVar()
                        checkbox_var.trace('w', lambda *args: update_selection_status())
                        video_checkboxes.append((checkbox_var, None, (i, entry)))
            
            # Filter entries
            videos_created = 0
            for checkbox_var, _, (i, entry) in video_checkboxes:
                if not entry:  # Skip None entries
                    continue
                    
                title = entry.get('title', 'Unknown Title')
                uploader = entry.get('uploader', 'Unknown')
                
                # Handle None values
                if title is None:
                    title = 'Unknown Title'
                if uploader is None:
                    uploader = 'Unknown'
                
                # Debug: Log each video being processed
                print(f"DEBUG: Processing video #{i}: {title[:50]}...")
                
                # Apply search filter
                if not filter_text or (filter_text.lower() in str(title).lower() or filter_text.lower() in str(uploader).lower()):
                    # Create frame for this video with constrained width
                    video_frame = tk.Frame(scrollable_frame, bg="#f8f9fa", relief="solid", bd=1, height=60)
                    video_frame.pack(fill=tk.X, pady=(1, 1), padx=5)
                    video_frame.pack_propagate(False)  # Maintain fixed height
                    
                    # Video info frame (takes most space)
                    info_frame = tk.Frame(video_frame, bg="#f8f9fa")
                    info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5), pady=8)
                    
                    # Checkbox for selection (on the right side)
                    checkbox = tk.Checkbutton(video_frame, variable=checkbox_var, bg="#f8f9fa")
                    checkbox.pack(side=tk.RIGHT, padx=(5, 10), pady=8)
                    
                    # Video title
                    title_text = f"#{i:03d} - {title}"
                    if len(title_text) > 80:
                        title_text = title_text[:77] + "..."
                    
                    title_label = tk.Label(info_frame, text=title_text, font=self.fonts['body'], 
                                         fg="#333333", bg="#f8f9fa", anchor="w")
                    title_label.pack(fill=tk.X)
                    
                    # Video details (duration, uploader)
                    duration = self.format_duration(entry.get('duration'))
                    views = self.format_views(entry.get('view_count'))
                    uploader_str = str(uploader) if uploader else 'Unknown'
                    uploader_display = uploader_str[:30] + "..." if len(uploader_str) > 30 else uploader_str
                    
                    details_text = f"⏱️ {duration} • 👤 {uploader_display}"
                    if views and views != "N/A":
                        details_text += f" • 👁️ {views}"
                    
                    details_label = tk.Label(info_frame, text=details_text, 
                                           font=self.fonts['small'], fg="#666666", bg="#f8f9fa", anchor="w")
                    details_label.pack(fill=tk.X, pady=(2, 0))
                    
                    # Update the checkbox reference
                    for idx, (var, _, entry_data) in enumerate(video_checkboxes):
                        if var is checkbox_var:
                            video_checkboxes[idx] = (var, checkbox, entry_data)
                            break
                    
                    # Add to filtered list
                    filtered_checkboxes.append((checkbox_var, checkbox, (i, entry)))
                    videos_created += 1
            
            # Update status labels
            total_count = len(all_entries)
            filtered_count = len(filtered_checkboxes)
            if filter_text:
                stats_label.config(text=f"{filtered_count}/{total_count} videos (filtered) • Channel: {self.current_playlist_info.get('uploader', 'Unknown')}")
            else:
                stats_label.config(text=f"{total_count} videos • Channel: {self.current_playlist_info.get('uploader', 'Unknown')}")
            
            # Update range end field default
            if not range_end.get():
                range_end.set(str(len(all_entries)))
            
            # Debug: Log how many videos were created
            print(f"DEBUG: Created {videos_created} video widgets out of {len(all_entries)} total entries")
            
            # Force canvas to update scroll region
            scrollable_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Force a canvas update to make sure everything is visible
            canvas.update_idletasks()
            
            update_selection_status()
        
        # Initial population
        populate_video_list()
        
        # Force initial canvas update
        playlist_window.update_idletasks()
        configure_scroll_region()
        
        # Bind search functionality with debouncing
        def on_search_change(*args):
            # Use after_idle to debounce search updates
            playlist_window.after_idle(lambda: populate_video_list(self.search_var.get()))
        
        self.search_var.trace('w', on_search_change)
        
        # Enhance mouse wheel scrolling by binding to the entire window area
        def bind_mousewheel_recursively(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux
            try:
                for child in widget.winfo_children():
                    bind_mousewheel_recursively(child)
            except:
                pass
        
        # Apply mouse wheel scrolling to the entire playlist window
        bind_mousewheel_recursively(playlist_window)
        
        # Initialize selected indices storage
        self.selected_playlist_indices = []
        
        # The button frame was already created earlier - no need to create it again
        
        def apply_selection():
            # Get selected videos
            selected_videos = []
            for var, _, (i, entry) in video_checkboxes:
                if var.get():
                    selected_videos.append(i)
            
            if not selected_videos:
                messagebox.showwarning("No Selection", "Please select at least one video to download.")
                return
            
            # Convert selected indices to range format for compatibility with existing download logic
            selected_videos.sort()
            
            # For now, we'll use the first and last selected indices as the range
            # This maintains compatibility with the existing range-based download system
            first_selected = min(selected_videos)
            last_selected = max(selected_videos)
            
            # Update main window range entries
            self.playlist_start_var.set(str(first_selected))
            self.playlist_end_var.set(str(last_selected))
            
            # Store the actual selected indices for more precise downloading
            self.selected_playlist_indices = selected_videos
            
            # Show selection info
            count = len(selected_videos)
            if count == 1:
                self.log_message(f"✓ Selected video #{selected_videos[0]} from playlist '{playlist_title[:30]}{'...' if len(playlist_title) > 30 else ''}'", "success")
            elif first_selected == last_selected or len(selected_videos) == (last_selected - first_selected + 1):
                # Consecutive range
                self.log_message(f"✓ Selected videos {first_selected}-{last_selected} ({count} videos) from playlist '{playlist_title[:30]}{'...' if len(playlist_title) > 30 else ''}'", "success")
            else:
                # Non-consecutive selection
                self.log_message(f"✓ Selected {count} videos from playlist '{playlist_title[:30]}{'...' if len(playlist_title) > 30 else ''}'", "success")
            
            playlist_window.destroy()
        
        # Now set the download button command
        download_btn.config(command=apply_selection)
            
    def analyze_url(self):
        """Analyze the YouTube URL and display video information"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return
            
        # Disable analyze button during analysis
        self.analyze_btn.config(state=tk.DISABLED)
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        # Show different message based on URL type for better user experience
        if 'playlist' in url or 'list=' in url:
            self.info_text.insert(tk.END, "🔍 Analyzing playlist (using fast mode for speed)...\n")
            self.log_message("🚀 Fast playlist analysis starting - this will be much quicker!", "info")
        else:
            self.info_text.insert(tk.END, "🔍 Analyzing video...\n")
        
        self.info_text.config(state=tk.DISABLED)
        
        # Run analysis in a separate thread
        thread = threading.Thread(target=self._analyze_url_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def test_formats(self):
        """Test available formats for the current URL"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL first")
            return
            
        self.log_message("Testing available formats...")
        thread = threading.Thread(target=self._test_formats_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _test_formats_thread(self, url):
        """Test formats in a separate thread"""
        try:
            ydl_opts = {
                'quiet': True,
                'listformats': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            self.root.after(0, self._display_formats, info)
            
        except Exception as e:
            self.root.after(0, self.log_message, f"Format test failed: {str(e)}")
            
    def _display_formats(self, info):
        """Display available formats"""
        formats = info.get('formats', [])
        if formats:
            format_info = "Available formats:\n"
            for fmt in formats[:10]:  # Show first 10 formats
                ext = fmt.get('ext', 'unknown')
                height = fmt.get('height', 'N/A')
                filesize = fmt.get('filesize')
                size_str = f" ({filesize//1024//1024}MB)" if filesize else ""
                format_info += f"  {ext} - {height}p{size_str}\n"
            
            if len(formats) > 10:
                format_info += f"  ... and {len(formats) - 10} more formats\n"
                
            self.log_message(format_info)
        else:
            self.log_message("No format information available")
        
    def _analyze_url_thread(self, url):
        """Analyze URL in a separate thread with fast playlist extraction"""
        try:
            # Check if this might be a playlist URL first
            is_likely_playlist = ('playlist' in url or 'list=' in url)
            
            if is_likely_playlist:
                # For playlists, use fast flat extraction first to get basic info
                self.root.after(0, self.log_message, "🔍 Analyzing playlist (fast mode)...", "info")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': 'in_playlist',  # Fast extraction for playlists
                    'skip_download': True,
                    'ignoreerrors': True,
                }
            else:
                # For single videos, do full extraction to get format information
                self.root.after(0, self.log_message, "🔍 Analyzing video and available formats...", "info")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'skip_download': True,
                    'ignoreerrors': True,
                    'listformats': False,  # We want format info but not to list them
                    # Remove extractor args that might limit format detection
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            # Update UI in main thread with success message
            if is_likely_playlist:
                self.root.after(0, self.log_message, "✓ Playlist analysis completed (fast mode)", "success")
            else:
                self.root.after(0, self.log_message, "✓ Video analysis completed", "success")
            
            self.root.after(0, self._display_video_info, info)
            
        except Exception as e:
            error_msg = f"Error analyzing URL: {str(e)}"
            self.root.after(0, self._display_error, error_msg)
            
    def _display_video_info(self, info):
        """Display video information in the UI"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        if not info:
            self.info_text.insert(tk.END, "Could not extract video information")
            self.info_text.config(state=tk.DISABLED)
            self.analyze_btn.config(state=tk.NORMAL)
            return
        
        # Store current playlist info for range selection
        self.current_playlist_info = info
        
        # Clear any previous individual video selections when analyzing new playlist
        self.selected_playlist_indices = []
        
        if 'entries' in info:  # Playlist
            playlist_title = info.get('title', 'Unknown Playlist')
            video_count = len([e for e in info['entries'] if e])  # Count non-None entries
            
            info_text = f"📋 PLAYLIST: {playlist_title}\n"
            info_text += f"📹 Videos: {video_count}\n"
            info_text += f"👤 Uploader: {info.get('uploader', 'Unknown')}\n"
            
            # Add performance note for large playlists
            if video_count > 20:
                info_text += f"⚡ Fast analysis mode used for large playlist\n"
            info_text += "\n"
            
            info_text += "📝 First few videos:\n"
            count = 0
            for i, entry in enumerate(info['entries']):
                if entry and count < 5:
                    # Handle both flat and full extraction data
                    title = entry.get('title', entry.get('url', 'Unknown Title'))
                    duration = self.format_duration(entry.get('duration')) if entry.get('duration') else "Unknown"
                    info_text += f"  {count+1}. {title} ({duration})\n"
                    count += 1
                    
            if video_count > 5:
                info_text += f"  ... and {video_count - 5} more videos\n"
            
            # Add note about downloading
            if video_count > 10:
                info_text += "\n💡 Tip: Use playlist range to download specific videos\n"
                
        else:  # Single video
            title = info.get('title', 'Unknown Title')
            uploader = info.get('uploader', 'Unknown')
            duration = self.format_duration(info.get('duration'))
            view_count = info.get('view_count', 0)
            upload_date = info.get('upload_date', '')
            
            info_text = f"🎬 VIDEO: {title}\n"
            info_text += f"👤 Uploader: {uploader}\n"
            info_text += f"⏱️ Duration: {duration}\n"
            
            if view_count:
                info_text += f"👁️ Views: {view_count:,}\n"
            
            if upload_date:
                try:
                    formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                    info_text += f"📅 Upload Date: {formatted_date}\n"
                except:
                    pass
                
            # Available formats
            formats = info.get('formats', [])
            if formats:
                info_text += "\n📺 Available qualities:\n"
                qualities = set()
                for fmt in formats:
                    if fmt.get('height'):
                        qualities.add(f"{fmt['height']}p")
                
                if qualities:
                    quality_list = sorted(qualities, key=lambda x: int(x[:-1]), reverse=True)
                    info_text += "  " + ", ".join(quality_list) + "\n"
        
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.NORMAL)
        
        # Update quality options with available formats
        self._update_quality_options(info)
        
        # Enable show playlist button if it's a playlist and playlist download is enabled
        if 'entries' in info and self.playlist_var.get():
            self.show_playlist_btn.config(state=tk.NORMAL)
        else:
            self.show_playlist_btn.config(state=tk.DISABLED)
        
    def _update_quality_options(self, info):
        """Update quality dropdown with actually available formats"""
        try:
            available_qualities = set()
            
            if 'entries' in info:  # Playlist
                # For playlists, we'll keep the default options since individual videos may vary
                # But we can add a note about this in the log
                self.log_message("🎥 Playlist detected: Quality options show common resolutions. Actual availability may vary per video.", "info")
                return  # Keep default quality options for playlists
            
            else:  # Single video
                formats = info.get('formats', [])
                
                # Extract unique video qualities
                video_qualities = set()
                audio_only = False
                
                for fmt in formats:
                    # Check for video formats with height
                    if fmt.get('height') and fmt.get('vcodec') != 'none':
                        height = fmt['height']
                        video_qualities.add(f"{height}p")
                    
                    # Check for audio-only formats
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        audio_only = True
                
                # Add found video qualities
                available_qualities.update(video_qualities)
                
                # Always add these standard options
                available_qualities.add("Data Saving")
                if audio_only:
                    available_qualities.add("Audio Only")
                
                # Convert to sorted list with better ordering
                quality_list = []
                
                # Start with "Best Quality" option
                quality_list.append("Best Quality")
                
                # Sort video qualities by resolution (highest first)
                video_resolutions = [q for q in available_qualities if q.endswith('p') and q != 'Data Saving']
                if video_resolutions:
                    sorted_video = sorted(video_resolutions, 
                                         key=lambda x: int(x[:-1]) if x[:-1].isdigit() else 0, 
                                         reverse=True)
                    quality_list.extend(sorted_video)
                
                # Add special options at the end
                quality_list.append("Data Saving")
                if "Audio Only" in available_qualities:
                    quality_list.append("Audio Only")
                
                # Update the combobox with available qualities
                if quality_list:
                    self.quality_combo['values'] = quality_list
                    
                    # Set the current selection to the best available quality
                    if quality_list and self.quality_var.get() not in quality_list:
                        # Set to "Best Quality" if current selection isn't available
                        self.quality_var.set("Best Quality")
                    
                    # Log available qualities
                    self.log_message(f"🎥 Available qualities updated: {', '.join(quality_list)}", "success")
                    
                    # Debug: Log all detected formats for troubleshooting
                    format_details = []
                    for fmt in formats[:15]:  # Show first 15 formats
                        height = fmt.get('height', 'N/A')
                        width = fmt.get('width', 'N/A')
                        ext = fmt.get('ext', 'unknown')
                        vcodec = fmt.get('vcodec', 'none')
                        acodec = fmt.get('acodec', 'none')
                        format_id = fmt.get('format_id', 'unknown')
                        
                        if height and height != 'N/A':
                            format_details.append(f"{height}p ({ext}, id:{format_id})")
                    
                    if format_details:
                        self.log_message(f"🔍 Debug - All detected video formats: {', '.join(format_details[:10])}", "info")
                        if len(format_details) > 10:
                            self.log_message(f"🔍 Debug - Plus {len(format_details) - 10} more formats...", "info")
                else:
                    # Fallback to defaults if no formats found
                    self.quality_combo['values'] = ["Best Quality", "720p", "480p", "360p", "240p", "Data Saving", "Audio Only"]
                    self.log_message("⚠️ Could not detect available qualities, using defaults", "warning")
                    
        except Exception as e:
            # Fallback to defaults on error
            self.quality_combo['values'] = ["Best Quality", "720p", "480p", "360p", "240p", "Data Saving", "Audio Only"]
            self.log_message(f"⚠️ Error updating quality options: {str(e)}, using defaults", "warning")
    
    def _display_error(self, error_msg):
        """Display error message"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, error_msg)
        self.info_text.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.NORMAL)
        
    def format_views(self, view_count):
        """Format view count for display"""
        if not view_count:
            return "N/A"
        
        if view_count >= 1000000:
            return f"{view_count/1000000:.1f}M"
        elif view_count >= 1000:
            return f"{view_count/1000:.1f}K"
        else:
            return str(view_count)
    
    def format_duration(self, seconds):
        """Format duration from seconds to readable format"""
        if not seconds:
            return "Unknown"
            
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except:
            return "Unknown"
            
    def is_valid_youtube_url(self, url):
        """Check if the URL is a valid YouTube URL"""
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/channel/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/@[\w-]+',
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
        
    def start_download(self):
        """Start the download process"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return
            
        # Create download directory if it doesn't exist
        download_dir = Path(self.download_path.get())
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create download directory: {str(e)}")
            return
            
        # Disable download button and enable stop button
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_downloading = True
        
        # Reset progress
        self.progress_var.set(0)
        self.status_label.config(text="Starting download...")
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _download_thread(self, url):
        """Download in a separate thread with multiple fallback strategies"""
        downloaded_files = set()  # Track downloaded files to prevent duplicates
        
        try:
            # Check for interruption before starting
            if not self.is_downloading:
                return
                
            format_selector = self._get_format_selector()
            
            # First, check if ffmpeg is available for merging
            ffmpeg_available = self._check_ffmpeg()
            
            # Use the working configuration from aggressive test
            ydl_opts = {
                'outtmpl': str(Path(self.download_path.get()) / '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': False,  # We want to see output, but this might help
                'ignoreerrors': True,  # Continue on errors like HTTP 403
                'retries': 3,  # Retry failed downloads
                'fragment_retries': 3,  # Retry failed fragments
                'extractor_retries': 2,  # Retry extractor failures
                'no_warnings': False,  # Show warnings for debugging
                'download_archive': None,  # Don't use download archive (prevents "already downloaded")
            }
            
            # Use the proper format selector based on FFmpeg availability
            if format_selector is not None:
                if not ffmpeg_available:
                    # No FFmpeg available - use audio-only which we know works
                    self.log_message("⚠️ FFmpeg not found - downloading AUDIO ONLY", "warning")
                    self.log_message("  → Modern YouTube videos need FFmpeg to combine video+audio streams", "info")
                    self.log_message("  → Restart the app to automatically install FFmpeg for video downloads", "info")
                    ydl_opts['format'] = 'bestaudio'  # Force audio-only
                    self.log_message("  → Using format: bestaudio (audio only)", "info")
                else:
                    # FFmpeg available - use the requested format selector as-is
                    ydl_opts['format'] = format_selector
                    self.log_message(f"✓ FFmpeg found - Using format: {format_selector}", "success")
                    if self.quality_var.get() != 'Audio Only':
                        self.log_message("  → Will attempt video+audio download", "info")
            
            # Only add subtitle options if requested
            if self.subtitle_var.get():
                ydl_opts['writesubtitles'] = True
                ydl_opts['writeautomaticsub'] = True
            
            # Handle playlist option and selection
            if not self.playlist_var.get():
                ydl_opts['noplaylist'] = True
            elif self.playlist_var.get():
                # Check if we have individually selected videos from the playlist selector
                if hasattr(self, 'selected_playlist_indices') and self.selected_playlist_indices:
                    # Use individually selected videos
                    indices_str = ','.join(map(str, self.selected_playlist_indices))
                    ydl_opts['playlist_items'] = indices_str
                    self.log_message(f"📋 Downloading {len(self.selected_playlist_indices)} selected videos: {indices_str}")
                    # Clear selection after use to prevent reuse
                    self.selected_playlist_indices = []
                elif self.playlist_start_var.get() or self.playlist_end_var.get():
                    # Fall back to range selection if no individual selection
                    start_num = 1
                    end_num = None
                    
                    if self.playlist_start_var.get():
                        try:
                            start_num = int(self.playlist_start_var.get())
                        except ValueError:
                            start_num = 1
                            
                    if self.playlist_end_var.get():
                        try:
                            end_num = int(self.playlist_end_var.get())
                        except ValueError:
                            end_num = None
                    
                    # Set playlist range in yt-dlp options
                    if end_num:
                        ydl_opts['playlist_items'] = f'{start_num}-{end_num}'
                        self.log_message(f"📋 Downloading playlist items {start_num} to {end_num}")
                    else:
                        ydl_opts['playlist_items'] = f'{start_num}-'
                        self.log_message(f"📋 Downloading playlist items from {start_num} to end")
                # If no selection at all, download the entire playlist
                else:
                    self.log_message(f"📋 Downloading entire playlist")
                
            # Note: Audio-only is now handled by format selector, no need for postprocessor
                
            self.log_message(f"🚀 Starting download: {url}")
            self.log_message(f"🎯 Format selector: {format_selector}")
            self.log_message(f"📁 Destination: {self.download_path.get()}")
            
            # Add custom progress hook to track files and detect already downloaded
            def enhanced_progress_hook(d):
                if not self.is_downloading:
                    raise KeyboardInterrupt("Download stopped by user")
                    
                if d['status'] == 'finished':
                    filename = d.get('filename', '')
                    if filename and filename not in downloaded_files:
                        downloaded_files.add(filename)
                        self.root.after(0, self.log_message, f"✅ Downloaded: {os.path.basename(filename)}", "success")
                elif d['status'] == 'error' and 'already been downloaded' in str(d.get('error', '')):
                    # Handle "already downloaded" case gracefully
                    filename = d.get('filename', '') or self._extract_filename_from_url(url)
                    self.root.after(0, self.log_message, f"📁 File already exists: {os.path.basename(filename)}", "info")
                    self.root.after(0, self.log_message, f"💡 Tip: Delete the file or choose a different quality to re-download", "info")
                        
                # Call the original progress hook
                self._progress_hook(d)
            
            # Keep the enhanced progress hook
            ydl_opts['progress_hooks'] = [enhanced_progress_hook]
            
            # Add a custom logger to catch "already downloaded" messages
            class AlreadyDownloadedLogger:
                def __init__(self, parent):
                    self.parent = parent
                    self.already_downloaded_detected = False
                    self.filename = None
                    
                def debug(self, msg):
                    if "has already been downloaded" in msg:
                        self.already_downloaded_detected = True
                        # Extract filename from message
                        import re
                        match = re.search(r'\[download\]\s+(.+?)\s+has already been downloaded', msg)
                        if match:
                            self.filename = match.group(1)
                        else:
                            # Try alternative pattern
                            if ".webm has already been downloaded" in msg or ".mp4 has already been downloaded" in msg:
                                self.filename = msg.split("has already been downloaded")[0].strip().split()[-1]
                        
                        # Log user-friendly message with orange warning color
                        filename_display = os.path.basename(self.filename) if self.filename else "video file"
                        self.parent.root.after(0, self.parent.log_message, f"📁 File already exists: {filename_display}", "warning")
                        self.parent.root.after(0, self.parent.log_message, f"💡 Located in: {self.parent.download_path.get()}", "warning")
                        self.parent.root.after(0, self.parent.log_message, f"🔄 To re-download: delete the file or choose different quality", "warning")
                        
                def info(self, msg): pass
                def warning(self, msg): pass  
                def error(self, msg): pass
                    
            custom_logger = AlreadyDownloadedLogger(self)
            ydl_opts['logger'] = custom_logger
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([url])
                    
                    # Check if file already existed
                    if custom_logger.already_downloaded_detected:
                        # File already existed - show custom completion message
                        if self.is_downloading:
                            self.root.after(0, self._download_already_complete)
                        return
                    
                except KeyboardInterrupt:
                    self.log_message("🛑 Download interrupted by user", "warning")
                    return
                except Exception as e:
                    if "403" in str(e) or "Forbidden" in str(e):
                        self.log_message(f"⚠️ HTTP 403 error - some videos may be restricted", "warning")
                        self.log_message(f"   This is often due to YouTube's anti-bot measures", "info")
                    raise  # Re-raise for main exception handler
                
            if self.is_downloading and downloaded_files:  # Check if not stopped and files were downloaded
                self.root.after(0, self._download_complete)
                self.root.after(0, self.log_message, f"🎉 Downloaded {len(downloaded_files)} file(s) successfully!", "success")
            elif self.is_downloading and not downloaded_files:
                self.root.after(0, self.log_message, "⚠️ No files were downloaded - check if videos are available", "warning")
                
        except KeyboardInterrupt:
            self.log_message("🛑 Download interrupted by user", "warning")
            self.root.after(0, self._cleanup_download)
            return
        except Exception as e:
            # Check for common errors and provide specific guidance
            error_str = str(e).lower()
            if "403" in error_str or "forbidden" in error_str:
                error_msg = "❌ HTTP 403 Forbidden - Some videos are restricted by YouTube's anti-bot measures"
                self.root.after(0, self.log_message, error_msg, "error")
                self.root.after(0, self.log_message, "💡 Try downloading individual videos instead of the whole playlist", "info")
            elif "unavailable" in error_str:
                error_msg = "❌ Video unavailable - This video may be private, deleted, or region-restricted"
                self.root.after(0, self.log_message, error_msg, "error")
            else:
                error_msg = f"Primary download failed: {str(e)[:200]}..."
                self.root.after(0, self.log_message, error_msg, "warning")
                self.root.after(0, self.log_message, "Trying fallback download method...", "info")
            
            # Only try fallbacks if not a permanent restriction
            if "403" not in error_str and "forbidden" not in error_str and downloaded_files == set():
                try:
                    self._fallback_download(url)
                    return  # If fallback succeeds, exit here
                except Exception as fallback_error:
                    # Try one more fallback with the exact working configuration
                    self.root.after(0, self.log_message, "Trying final desperate fallback...", "warning")
                    try:
                        self._desperate_fallback(url)
                        return  # If desperate fallback succeeds, exit here
                    except Exception as desperate_error:
                        final_error = f"All download methods failed. Primary: {str(e)[:100]}. Fallback: {str(fallback_error)[:100]}. Desperate: {str(desperate_error)[:100]}"
                        self.root.after(0, self._download_error, final_error)
                        self.root.after(0, self.log_message, f"All methods exhausted", "error")
            else:
                # For 403 errors, just report the error without trying fallbacks
                final_error = str(e)
                self.root.after(0, self._download_error, final_error)
        finally:
            # Always ensure download state is cleaned up
            if not self.is_downloading:
                self.root.after(0, self._cleanup_download)
            
    def _cleanup_download(self):
        """Clean up download state after completion, cancellation, or error"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_icon.config(text="⏸️", foreground=self.colors['text_secondary'])
        self.status_label.config(text="Ready", foreground=self.colors['text'])
        
    def _fallback_download(self, url):
        """Fallback download method with minimal options and specific format fallbacks"""
        # Updated fallback strategies based on diagnostic results
        fallback_formats = [
            'bestaudio',  # This works reliably for audio
            '602+139-drc',  # Specific working video+audio combination
            'bestvideo+bestaudio',  # Generic video+audio
            '602',        # Specific working video-only
            '139-drc',    # Specific working audio-only
        ]
        
        for i, fmt in enumerate(fallback_formats):
            if not self.is_downloading:  # Check if user stopped
                return
                
            try:
                # Minimal yt-dlp options like the working test
                ydl_opts = {
                    'format': fmt,
                    'outtmpl': str(Path(self.download_path.get()) / f'%(title)s_fallback{i+1}.%(ext)s'),
                    'progress_hooks': [self._progress_hook],
                }
                
                if not self.playlist_var.get():
                    ydl_opts['noplaylist'] = True
                    
                self.root.after(0, self.log_message, f"Fallback attempt {i+1}: Using format '{fmt}'...", "info")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    
                if self.is_downloading:
                    self.root.after(0, self._download_complete)
                    self.root.after(0, self.log_message, f"✓ Fallback success with format: {fmt}", "success")
                return  # Success, exit fallback attempts
                
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                self.root.after(0, self.log_message, f"Fallback {i+1} failed: {error_msg}", "warning")
                continue  # Try next format
        
        # If we get here, all fallbacks failed
        raise Exception("All fallback formats failed")
    
    def _desperate_fallback(self, url):
        """Last resort fallback using exact configuration that worked in test"""
        try:
            # Use the EXACT configuration from aggressive_test.py that worked
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': str(Path(self.download_path.get()) / '%(title)s_desperate.%(ext)s'),
                'quiet': True,  # This was the key difference that made it work
            }
            
            if not self.playlist_var.get():
                ydl_opts['noplaylist'] = True
                
            self.root.after(0, self.log_message, "Desperate fallback: Using exact working config (bestaudio, quiet=True)", "info")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if self.is_downloading:
                self.root.after(0, self._download_complete)
                self.root.after(0, self.log_message, "✓ Desperate fallback SUCCESS! (audio-only)", "success")
                
        except Exception as e:
            raise Exception(f"Desperate fallback failed: {str(e)}")
    
    def _setup_local_ffmpeg(self):
        """Setup local FFmpeg installation if available"""
        try:
            project_root = Path(__file__).parent
            
            # Priority 1: Check venv/ffmpeg (setup.py installed)
            venv_ffmpeg_path = project_root / "venv" / "ffmpeg"
            if venv_ffmpeg_path.exists() and (venv_ffmpeg_path / "ffmpeg.exe").exists():
                # Add venv FFmpeg to PATH for this session
                import os
                current_path = os.environ.get('PATH', '')
                if str(venv_ffmpeg_path) not in current_path:
                    os.environ['PATH'] = f"{venv_ffmpeg_path};{current_path}"
                print(f"✓ Using setup FFmpeg from: {venv_ffmpeg_path}")
                return
                
            # Priority 2: Check if FFmpeg is in system PATH
            import subprocess
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=3)
                print(f"✓ Using system FFmpeg from PATH")
                return
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                
            print("ℹ FFmpeg not found - app will automatically install it on restart")
            print("ℹ For now, app will work with audio-only downloads for some videos")
            
        except Exception as e:
            print(f"Could not setup FFmpeg: {e}")
            
    def _progress_hook(self, d):
        """Enhanced progress hook for yt-dlp that handles HLS fragment downloads"""
        # Check if download was cancelled
        if not self.is_downloading:
            raise KeyboardInterrupt("Download cancelled by user")
            
        # Debug logging for progress data (only log every 100th call to avoid spam)
        if not hasattr(self, '_progress_debug_counter'):
            self._progress_debug_counter = 0
        self._progress_debug_counter += 1
        
        # Log progress data occasionally for debugging
        if self._progress_debug_counter % 100 == 0 or d['status'] != 'downloading':
            debug_info = {
                'status': d.get('status'),
                'has_total_bytes': 'total_bytes' in d,
                'has_estimate': 'total_bytes_estimate' in d,
                'has_fragments': 'fragment_count' in d,
                'has_percent': '_percent_str' in d
            }
            if 'fragment_index' in d and 'fragment_count' in d:
                debug_info['fragment_progress'] = f"{d['fragment_index']}/{d['fragment_count']}"
            print(f"Progress debug: {debug_info}")
            
        if d['status'] == 'downloading':
            progress = 0
            
            # Method 1: Standard total_bytes calculation (works for most downloads)
            if 'total_bytes' in d and d['total_bytes'] and d['total_bytes'] > 0:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.root.after(0, self._update_progress, progress, d)
                
            # Method 2: Estimated total for HLS/fragment downloads
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] and d['total_bytes_estimate'] > 0:
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                self.root.after(0, self._update_progress, progress, d)
                
            # Method 3: Fragment-based progress for HLS streams
            elif 'fragment_index' in d and 'fragment_count' in d:
                if d['fragment_count'] and d['fragment_count'] > 0:
                    fragment_progress = (d['fragment_index'] / d['fragment_count']) * 100
                    # Add partial progress within current fragment if available
                    if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                        fragment_partial = (d['downloaded_bytes'] / d['total_bytes']) * (100 / d['fragment_count'])
                        progress = fragment_progress + fragment_partial
                    else:
                        progress = fragment_progress
                    self.root.after(0, self._update_progress, progress, d)
                    
            # Method 4: Fallback to percent string parsing
            elif '_percent_str' in d:
                percent_str = d['_percent_str'].strip()
                if percent_str and percent_str != 'N/A' and percent_str != 'Unknown':
                    try:
                        progress = float(percent_str.replace('%', ''))
                        self.root.after(0, self._update_progress, progress, d)
                    except (ValueError, TypeError):
                        pass
                        
            # Method 5: Manual calculation for edge cases
            elif 'downloaded_bytes' in d and d['downloaded_bytes']:
                # For streams without total size, show activity with a pulsing progress
                # This prevents the progress bar from staying at 0% during long downloads
                estimated_progress = min(50, (d['downloaded_bytes'] / (1024 * 1024)) * 2)  # 2% per MB
                self.root.after(0, self._update_progress, estimated_progress, d)
                
        elif d['status'] == 'error':
            error_msg = d.get('error', 'Unknown download error')
            if "403" in str(error_msg) or "Forbidden" in str(error_msg):
                self.root.after(0, self.log_message, f"⚠️ HTTP 403 error for: {os.path.basename(d.get('filename', 'unknown'))}", "warning")
            else:
                self.root.after(0, self.log_message, f"❌ Error downloading: {os.path.basename(d.get('filename', 'unknown'))}", "error")
        elif d['status'] == 'finished':
            filename = os.path.basename(d['filename'])
            # This logging is now handled by the enhanced_progress_hook to prevent duplicates
            
    def _update_progress(self, progress, d):
        """Update progress bar and status with visual indicators and enhanced HLS support"""
        self.progress_var.set(progress)
        
        # Update status icon based on progress
        if progress < 25:
            self.status_icon.config(text="🔄", foreground=self.colors['primary'])
        elif progress < 50:
            self.status_icon.config(text="⏳", foreground=self.colors['warning'])
        elif progress < 75:
            self.status_icon.config(text="⏰", foreground=self.colors['warning'])
        else:
            self.status_icon.config(text="⏱️", foreground=self.colors['success'])
        
        filename = os.path.basename(d.get('filename', ''))
        speed = d.get('_speed_str', '')
        eta = d.get('_eta_str', '')
        
        # Truncate long filenames
        if len(filename) > 50:
            filename = filename[:47] + "..."
        
        # Build status with different information based on download type
        status = f"Downloading: {filename}"
        
        # Show fragment info for HLS downloads
        if 'fragment_index' in d and 'fragment_count' in d:
            fragment_info = f"Fragment {d['fragment_index']}/{d['fragment_count']}"
            status += f" | 🧩 {fragment_info}"
        
        # Show speed if available
        if speed and speed != 'N/A':
            status += f" | 📡 {speed}"
            
        # Show ETA if available and meaningful
        if eta and eta != 'N/A' and eta != 'Unknown':
            status += f" | ⏰ {eta}"
            
        # Show progress percentage
        if progress > 0:
            status += f" | {progress:.1f}%"
        
        # Add download method indicator
        if 'fragment_count' in d:
            status += " (HLS)"
        elif 'total_bytes_estimate' in d:
            status += " (Est.)"
            
        self.status_label.config(text=status, foreground=self.colors['primary'])
        
    def _download_already_complete(self):
        """Handle completion when file was already downloaded"""
        self.progress_var.set(100)
        
        # Update status with "already downloaded" indicators
        self.status_icon.config(text="📁", foreground=self.colors['warning'])
        self.status_label.config(text="📁 Downloaded Already!", 
                               foreground=self.colors['warning'])
        
        self.log_message("📁 Downloaded Already - file exists in destination folder", "warning")
        
        # Re-enable download button and show open folder button
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.open_folder_btn.grid()  # Show the open folder button
        self.is_downloading = False
        
        # Show "already downloaded" message
        messagebox.showinfo("Already Downloaded", "This video was already downloaded!\n\nThe file exists in your download folder.")
        
        # Open the download folder
        if messagebox.askyesno("Open Folder", "Would you like to open the download folder?"):
            try:
                import os
                os.startfile(self.download_path.get())
            except Exception as e:
                try:
                    subprocess.Popen(['explorer', self.download_path.get()])
                except:
                    self.log_message(f"Could not open folder: {self.download_path.get()}")
    
    def _download_complete(self):
        """Handle download completion with enhanced status display"""
        self.progress_var.set(100)
        
        # Update status with success indicators
        self.status_icon.config(text="✅", foreground=self.colors['success'])
        self.status_label.config(text="✓ Download completed successfully!", 
                               foreground=self.colors['success'])
        
        self.log_message("🎉 Download completed successfully!", "success")
        
        # Re-enable download button and show open folder button
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.open_folder_btn.grid()  # Show the open folder button
        self.is_downloading = False
        
        # Show completion message
        messagebox.showinfo("Success", "Download completed successfully!")
        
        # Open the download folder
        if messagebox.askyesno("Open Folder", "Would you like to open the download folder?"):
            try:
                import os
                os.startfile(self.download_path.get())
            except Exception as e:
                try:
                    subprocess.Popen(['explorer', self.download_path.get()])
                except:
                    self.log_message(f"Could not open folder: {self.download_path.get()}")
        
    def _download_error(self, error_msg):
        """Handle download error with enhanced error display"""
        # Update status with error indicators
        self.status_icon.config(text="❌", foreground=self.colors['error'])
        self.status_label.config(text="⚠ Download failed!", 
                               foreground=self.colors['error'])
        
        self.log_message(f"❌ {error_msg}", "error")
        
        # Re-enable download button
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.is_downloading = False
        
        # Show error message
        messagebox.showerror("Download Error", f"Download failed:\n\n{error_msg}\n\nThis might be due to YouTube's anti-bot measures. Try a different video or quality setting.")
        
    def stop_download(self):
        """Stop the current download with enhanced status display"""
        if not self.is_downloading:
            return
            
        self.log_message("🛑 Stopping download... (may take a moment)", "warning")
        self.is_downloading = False
        
        # Update status with stop indicators
        self.status_icon.config(text="⏹️", foreground=self.colors['warning'])
        self.status_label.config(text="⏹️ Stopping download...", 
                               foreground=self.colors['warning'])
        
        # Disable stop button to prevent multiple clicks
        self.stop_btn.config(state=tk.DISABLED)
        
        # The actual cleanup will be done in _cleanup_download via the download thread
        
    def _get_format_selector(self):
        """Get format selector that works with modern YouTube DASH streams"""
        quality = self.quality_var.get()
        
        # Handle new user-friendly quality options
        if quality == 'Audio Only':
            # Use proven working audio format
            return 'bestaudio'
        elif quality == 'Data Saving':
            # Use specific working format IDs for lowest quality (data saving)
            return 'worstvideo[height>=144]+bestaudio/602+139-drc/602+139/602/160+139/160/bestaudio'
        elif quality == 'Best Quality':
            # Use best available quality with working fallbacks
            return 'bestvideo+bestaudio/best[height<=2160]/bestvideo[height<=1440]+bestaudio/bestvideo[height<=1080]+bestaudio/bestvideo+bestaudio/bestaudio'
        elif quality == '720p':
            # Use specific working format combinations for 720p
            return 'bestvideo[height<=720]+bestaudio/136+140/136+139/bestaudio'
        elif quality == '480p':
            # Use specific working format combinations for 480p
            return 'bestvideo[height<=480]+bestaudio/135+140/135+139/bestaudio'
        elif quality == '360p':
            # Use specific working format combinations for 360p
            return 'bestvideo[height<=360]+bestaudio/134+140/134+139/bestaudio'
        elif quality == '240p':
            # Use specific working format combinations for 240p
            return 'bestvideo[height<=240]+bestaudio/133+140/133+139/bestaudio'
        elif quality.endswith('p') and quality[:-1].isdigit():
            # Handle dynamic resolution options (e.g., "1080p", "1440p")
            height = quality[:-1]
            return f'bestvideo[height<={height}]+bestaudio/bestvideo[height<={height}]/bestaudio'
        else:
            # Fallback to best quality
            return 'bestvideo+bestaudio/bestaudio'
    
    def _check_ffmpeg(self):
        """Check if ffmpeg is available for merging video+audio"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_no_merge_format_selector(self):
        """Get format selector that doesn't require merging (for when ffmpeg is missing)"""
        quality = self.quality_var.get()
        
        # Simple single-file formats when FFmpeg is not available - prefer audio
        if quality == 'Audio Only':
            return 'bestaudio'  # Audio-only format
        elif quality == 'Data Saving':
            return 'worst/bestaudio'  # Lowest quality or audio fallback
        elif quality == 'Best Quality':
            return 'best/bestaudio'  # Best single file or audio fallback
        else:
            # For all other qualities, fallback to audio when FFmpeg is missing
            return 'bestaudio'  # Audio is better than no download
        
    def reset_all_options(self):
        """Reset all options to default values when app starts"""
        try:
            # Reset all variables to default values
            self.url_var.set("")  # Clear URL field
            self.quality_var.set("Best Quality")  # Default quality
            self.format_var.set("any")  # Default format
            self.subtitle_var.set(False)  # No subtitles by default
            self.playlist_var.set(False)  # Single video mode by default (unchecked)
            self.playlist_start_var.set("1")  # Start from first video
            self.playlist_end_var.set("")  # No end limit
            
            # Reset download path to project directory
            project_downloads = Path(__file__).parent / "downloads"
            project_downloads.mkdir(exist_ok=True)
            self.download_path.set(str(project_downloads))
            
            # Clear any cached playlist data
            self.current_playlist_info = None
            self.selected_playlist_indices = []
            
            # Reset download state
            self.is_downloading = False
            
            # Reset progress display if widgets exist
            if hasattr(self, 'progress_var'):
                self.progress_var.set(0)
            
            # Reset status display if widgets exist
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Ready to download", 
                                       foreground=self.colors['text'])
            
            if hasattr(self, 'status_icon'):
                self.status_icon.config(text="📥", foreground=self.colors['primary'])
            
            # Reset quality dropdown to defaults
            if hasattr(self, 'quality_combo'):
                self.quality_combo['values'] = ["Best Quality", "720p", "480p", "360p", "240p", "Data Saving", "Audio Only"]
            
            # Clear yt-dlp download archive to avoid "already downloaded" issues
            try:
                import os
                archive_files = [
                    '.yt-dlp-archive',
                    '.youtube-dl-archive', 
                    'archive.txt'
                ]
                for archive_file in archive_files:
                    if os.path.exists(archive_file):
                        os.remove(archive_file)
                        print(f"Cleared download archive: {archive_file}")
            except Exception as e:
                print(f"Could not clear download archives: {e}")
            
            # Clear log if it exists
            if hasattr(self, 'log_text'):
                self.log_text.delete(1.0, tk.END)
                self.log_message("✨ All options reset to defaults", "info")
                
            print("✅ All options reset to defaults")
            
        except Exception as e:
            print(f"⚠️ Error resetting options: {str(e)}")
    
    def manual_reset_options(self):
        """Manual reset triggered by user button/shortcut"""
        if self.is_downloading:
            messagebox.showwarning("Cannot Reset", "Cannot reset options while downloading. Please stop the download first.")
            return
            
        # Ask for confirmation
        if not messagebox.askyesno("Confirm Reset", 
                                 "Reset all options to defaults?\n\n"
                                 "This will reset:\n"
                                 "• URL field\n"
                                 "• Quality settings\n"
                                 "• Format settings\n"
                                 "• Subtitle options\n"
                                 "• Playlist settings (unchecked)\n"
                                 "• Download path to default\n"
                                 "• Progress and log\n"):
            return
            
        # Perform reset
        self.reset_all_options()
        self.log_message("✨ All options manually reset to defaults", "success")
    
    def load_settings(self):
        """Load settings from file - but keep reset defaults"""
        try:
            # Don't load any settings - keep everything reset to defaults
            # This ensures fresh start every time the app launches
            pass
                
        except Exception as e:
            self.log_message(f"Could not load settings: {str(e)}")
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'download_path': self.download_path.get(),
                'quality': self.quality_var.get(),
                'format': self.format_var.get(),
                'subtitles': self.subtitle_var.get(),
                'playlist': self.playlist_var.get(),
                'playlist_start': self.playlist_start_var.get(),
                'playlist_end': self.playlist_end_var.get(),
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            self.log_message(f"Could not save settings: {str(e)}")
            
    def on_closing(self):
        """Handle application closing"""
        if self.is_downloading:
            if messagebox.askokcancel("Quit", "Download in progress. Do you want to quit?"):
                self.is_downloading = False
                self.save_settings()
                self.root.destroy()
        else:
            self.save_settings()
            self.root.destroy()
            
    def run(self):
        """Run the application"""
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the GUI event loop
        self.root.mainloop()

def main():
    """Main entry point for the application"""
    try:
        app = YouTubeDownloader()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user (Ctrl+C)")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("Please report this error if it persists.")

if __name__ == "__main__":
    main()
