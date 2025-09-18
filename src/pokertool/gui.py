from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import time
from typing import Optional, List, Dict, Any

from .error_handling import sanitize_input, log, run_safely, retry_on_failure, CircuitBreaker
from .storage import get_secure_db, SecurityError

class SecureGUI:
    """Enhanced GUI with security features and better user experience."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.secure_db = get_secure_db()
        self.circuit_breaker = CircuitBreaker()
        self.session_id: Optional[str] = None
        self.analysis_count = 0
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface with security enhancements."""
        self.root.title('PokerTool - Enhanced Security Version')
        self.root.geometry('800x600')
        self.root.minsize(600, 400)
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Input section
        self.create_input_section(main_frame)
        
        # Analysis output
        self.create_output_section(main_frame)
        
        # History section
        self.create_history_section(main_frame)
        
        # Status bar
        self.create_status_bar()
        
        # Menu bar
        self.create_menu_bar()
        
        # Initialize session
        self.start_new_session()
        
    def create_input_section(self, parent: ttk.Frame) -> None:
        """Create the input section with validation."""
        input_frame = ttk.LabelFrame(parent, text="Hand Analysis", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # Hand input
        ttk.Label(input_frame, text='Hand (e.g., AsKh):').grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.hand_var = tk.StringVar()
        self.hand_entry = ttk.Entry(input_frame, textvariable=self.hand_var, width=30)
        self.hand_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.hand_entry.bind('<KeyRelease>', self._validate_hand_input)
        
        # Board input
        ttk.Label(input_frame, text='Board (e.g., 7d8d9c):').grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.board_var = tk.StringVar()
        self.board_entry = ttk.Entry(input_frame, textvariable=self.board_var, width=30)
        self.board_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        self.board_entry.bind('<KeyRelease>', self._validate_board_input)
        
        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.analyze_btn = ttk.Button(button_frame, text='Analyze Hand', command=self.analyze_hand)
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(button_frame, text='Save Analysis', command=self.save_analysis, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text='Clear', command=self.clear_inputs)
        self.clear_btn.pack(side=tk.LEFT)
        
    def create_output_section(self, parent: ttk.Frame) -> None:
        """Create the analysis output section."""
        output_frame = ttk.LabelFrame(parent, text="Analysis Result", padding="10")
        output_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=10, 
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_history_section(self, parent: ttk.Frame) -> None:
        """Create the hand history section."""
        history_frame = ttk.LabelFrame(parent, text="Recent Analyses", padding="10")
        history_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Treeview for history
        columns = ('Time', 'Hand', 'Board', 'Result')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # History control buttons
        history_btn_frame = ttk.Frame(history_frame)
        history_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(history_btn_frame, text='Refresh History', command=self.load_history).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(history_btn_frame, text='Export History', command=self.export_history).pack(side=tk.LEFT)
        
    def create_status_bar(self) -> None:
        """Create status bar for user feedback."""
        self.status_var = tk.StringVar()
        self.status_var.set('Ready - Session not started')
        
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Analysis counter
        self.counter_var = tk.StringVar()
        self.counter_var.set('Analyses: 0')
        ttk.Label(status_frame, textvariable=self.counter_var, relief=tk.SUNKEN).grid(row=0, column=1, padx=(5, 0))
        
    def create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.start_new_session)
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Screen Scraper", command=self.launch_scraper)
        tools_menu.add_command(label="Database Cleanup", command=self.cleanup_database)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def _validate_hand_input(self, event=None) -> None:
        """Validate hand input in real-time."""
        hand = self.hand_var.get()
        if hand and len(hand) >= 2:
            try:
                sanitized = sanitize_input(hand, max_length=50)
                if sanitized != hand:
                    self.hand_var.set(sanitized)
                    self.update_status("Hand input was sanitized", "warning")
            except ValueError as e:
                self.update_status(f"Invalid hand input: {e}", "error")
                
    def _validate_board_input(self, event=None) -> None:
        """Validate board input in real-time."""
        board = self.board_var.get()
        if board:
            try:
                sanitized = sanitize_input(board, max_length=50)
                if sanitized != board:
                    self.board_var.set(sanitized)
                    self.update_status("Board input was sanitized", "warning")
            except ValueError as e:
                self.update_status(f"Invalid board input: {e}", "error")
                
    @retry_on_failure(max_retries=3)
    def analyze_hand(self) -> None:
        """Analyze the poker hand with security and error handling."""
        hand = self.hand_var.get().strip()
        board = self.board_var.get().strip() or None
        
        if not hand:
            messagebox.showwarning("Input Required", "Please enter a hand to analyze")
            return
            
        try:
            # Use circuit breaker for analysis
            result = self.circuit_breaker.call(self._safe_analyse, hand, board)
            
            # Display result
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, result)
            self.output_text.config(state=tk.DISABLED)
            
            # Enable save button
            self.save_btn.config(state='normal')
            self.current_analysis = {
                'hand': hand,
                'board': board,
                'result': result,
                'timestamp': time.time()
            }
            
            self.analysis_count += 1
            self.counter_var.set(f'Analyses: {self.analysis_count}')
            self.update_status("Analysis completed successfully", "success")
            
        except SecurityError as e:
            messagebox.showerror("Security Error", f"Security violation detected: {e}")
            log.warning("Security violation in GUI: %s", e)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Analysis failed: {e}")
            self.update_status(f"Analysis failed: {e}", "error")
            
    def _safe_analyse(self, hand: str, board: Optional[str]) -> str:
        """Safely analyze hand with input validation."""
        try:
            # Sanitize inputs
            hand = sanitize_input(hand, max_length=50)
            if board:
                board = sanitize_input(board, max_length=50)
                
            # Try to import and use the core analysis function
            try:
                from .core import analyse_hand
                result = analyse_hand(hand, board)
                return str(result)
            except ImportError:
                # Fallback analysis if core module isn't available
                return f'[STUB] Analysis for hand={hand}, board={board}\n\nThis is a placeholder analysis.\nThe actual poker analysis engine is not yet implemented.'
                
        except Exception as e:
            raise Exception(f"Analysis error: {e}") from e
            
    def save_analysis(self) -> None:
        """Save the current analysis to the secure database."""
        if not hasattr(self, 'current_analysis'):
            messagebox.showwarning("Nothing to Save", "No analysis to save")
            return
            
        try:
            analysis = self.current_analysis
            record_id = self.secure_db.save_hand_analysis(
                hand=analysis['hand'],
                board=analysis['board'],
                result=analysis['result'],
                session_id=self.session_id
            )
            
            messagebox.showinfo("Saved", f"Analysis saved with ID: {record_id}")
            self.save_btn.config(state='disabled')
            self.load_history()  # Refresh history
            self.update_status("Analysis saved to database", "success")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save analysis: {e}")
            self.update_status(f"Save failed: {e}", "error")
            
    def clear_inputs(self) -> None:
        """Clear all input fields and output."""
        self.hand_var.set('')
        self.board_var.set('')
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.save_btn.config(state='disabled')
        self.update_status("Inputs cleared", "info")
        
    def load_history(self) -> None:
        """Load recent hand history from database."""
        try:
            hands = self.secure_db.get_recent_hands(limit=50)
            
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
                
            # Add new items
            for hand in hands:
                timestamp = hand.get('timestamp', 'Unknown')
                if isinstance(timestamp, str) and timestamp != 'Unknown':
                    # Parse timestamp if it's a string
                    try:
                        import datetime
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        display_time = dt.strftime('%H:%M:%S')
                    except:
                        display_time = timestamp[:8] if len(timestamp) > 8 else timestamp
                else:
                    display_time = 'Unknown'
                    
                self.history_tree.insert('', 'end', values=(
                    display_time,
                    hand.get('hand_text', 'N/A'),
                    hand.get('board_text', 'N/A') or '-',
                    (hand.get('analysis_result', 'N/A') or 'N/A')[:50] + ('...' if len(str(hand.get('analysis_result', ''))) > 50 else '')
                ))
                
            self.update_status(f"Loaded {len(hands)} recent analyses", "info")
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load history: {e}")
            
    def start_new_session(self) -> None:
        """Start a new game session."""
        try:
            self.session_id = self.secure_db.create_session(
                notes=f"GUI session started at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.analysis_count = 0
            self.counter_var.set('Analyses: 0')
            self.update_status(f"New session started: {self.session_id[:8]}", "success")
            self.load_history()
        except Exception as e:
            messagebox.showerror("Session Error", f"Failed to start session: {e}")
            
    def backup_database(self) -> None:
        """Create a database backup."""
        try:
            backup_path = self.secure_db.backup_database()
            messagebox.showinfo("Backup Created", f"Database backed up to:\n{backup_path}")
            self.update_status(f"Database backed up", "success")
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to backup database: {e}")
            
    def cleanup_database(self) -> None:
        """Clean up old database records."""
        result = messagebox.askyesno(
            "Cleanup Database", 
            "This will remove old records (older than 30 days).\nContinue?"
        )
        if result:
            try:
                deleted_count = self.secure_db.cleanup_old_data()
                messagebox.showinfo("Cleanup Complete", f"Removed {deleted_count} old records")
                self.load_history()  # Refresh history
                self.update_status(f"Cleaned up {deleted_count} old records", "success")
            except Exception as e:
                messagebox.showerror("Cleanup Error", f"Failed to cleanup database: {e}")
                
    def launch_scraper(self) -> None:
        """Launch the screen scraper (placeholder)."""
        try:
            from . import scrape
            result = scrape.run_screen_scraper()
            messagebox.showinfo('Screen Scraper', f'Scraper result: {result}')
        except ImportError:
            messagebox.showinfo('Screen Scraper', 'Screen scraper module not available')
        except Exception as e:
            messagebox.showerror('Screen Scraper Error', f'Scraper failed: {e}')
            
    def export_history(self) -> None:
        """Export analysis history to file."""
        try:
            import csv
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                hands = self.secure_db.get_recent_hands(limit=1000)
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Hand', 'Board', 'Analysis Result'])
                    
                    for hand in hands:
                        writer.writerow([
                            hand.get('timestamp', ''),
                            hand.get('hand_text', ''),
                            hand.get('board_text', '') or '',
                            hand.get('analysis_result', '') or ''
                        ])
                        
                messagebox.showinfo("Export Complete", f"History exported to {filename}")
                self.update_status(f"History exported to file", "success")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export history: {e}")
            
    def show_about(self) -> None:
        """Show about dialog."""
        about_text = """PokerTool Enhanced Security Version
        
Version: 21.0.0
Features:
• Secure input validation
• SQL injection prevention
• Rate limiting protection
• Automatic error recovery
• Comprehensive logging
• Database backup & cleanup

Built with security and reliability in mind."""
        
        messagebox.showinfo("About PokerTool", about_text)
        
    def update_status(self, message: str, level: str = "info") -> None:
        """Update status bar with colored message."""
        timestamp = time.strftime('%H:%M:%S')
        status_message = f"[{timestamp}] {message}"
        self.status_var.set(status_message)
        
        # Log the status update
        if level == "error":
            log.error("GUI Status: %s", message)
        elif level == "warning":
            log.warning("GUI Status: %s", message)
        else:
            log.info("GUI Status: %s", message)
            
    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()

def main() -> int:
    """Main GUI entry point with enhanced security."""
    def create_and_run_gui():
        gui = SecureGUI()
        gui.run()
        return 0
    
    return run_safely(create_and_run_gui)

# Legacy function names for backward compatibility
def run() -> int:
    """Legacy entry point."""
    return main()

# Legacy functions for backward compatibility
def _safe_analyse(hand: str, board: str | None) -> str:
    """Legacy function - use SecureGUI instead."""
    try:
        hand = sanitize_input(hand, max_length=50)
        if board:
            board = sanitize_input(board, max_length=50)
            
        try:
            from .core import analyse_hand
            result = analyse_hand(hand, board)
            return str(result)
        except ImportError:
            return f'[stub] analysed hand={hand!r} board={board!r}'
    except Exception as e:
        return f'[error] {e}'

def _on_analyse(hand_var: tk.StringVar, board_var: tk.StringVar, output: tk.Text) -> None:
    """Legacy function - use SecureGUI instead."""
    hand = hand_var.get().strip()
    board = board_var.get().strip() or None
    try:
        res = _safe_analyse(hand, board)
        output.delete('1.0', tk.END)
        output.insert(tk.END, res)
    except Exception as e:
        messagebox.showerror('PokerTool', f"Analysis failed: \n{e}")

def _on_scrape() -> None:
    """Legacy function - use SecureGUI instead."""
    try:
        from . import scrape
        res = scrape.run_screen_scraper()
        messagebox.showinfo('Screen Scraper', str(res))
    except Exception as e:
        messagebox.showerror('Screen Scraper', f"Scraper failed: \n{e}")

if __name__ == '__main__':
    raise SystemExit(main())
