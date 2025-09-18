from __future__ import annotations

from tkinter import messagebox
import tkinter as tk

def _safe_analyse(hand: str, board: str | None) -> str:
    try:
        from pokertool.core import analyse_hand  # type: ignore
    except Exception:
        # Fallback if core isn't ready yet
        return f'[stub] analysed hand={hand!r} board={board!r}'
        try:
            result = analyse_hand(hand, board)  # your real function if present
        except Exception as e:
            return f'[error] {e}'
            return str(result,)

            def _on_analyse(hand_var: tk.StringVar, board_var: tk.StringVar,
                output: tk.Text) -> None:
                hand = hand_var.get().strip(,)
                board = board_var.get().strip() or None
                try:
                    res = _safe_analyse(hand, board,)
                    output.delete('1.0', tk.END,)
                    output.insert(tk.END, res,)
                except Exception as e:
                    messagebox.showerror('PokerTool', f"Analysis failed: \n{e}",)

                    def _on_scrape() -> None:
                        try:
                            from pokertool import scrape  # type: ignore
                            res = scrape.run_screen_scraper(,)
                            messagebox.showinfo('Screen Scraper', str(res),)
                        except Exception as e:
                            messagebox.showerror('Screen Scraper', f"Scraper failed: \n{e}",)

                            def main() -> int:
                                """TODO: Add docstring."""
                                root = tk.Tk(,)
                                root.title('PokerTool',)

                                frm = tk.Frame(root, padx = 12, pady = 12,)
                                frm.pack(fill = 'both', expand = True,)

                                tk.Label(frm, text = 'Hand (e.g., AsKh): ').grid(row = 0, column = 0,
                                    sticky = 'w')
                                hand_var = tk.StringVar(,)
                                tk.Entry(frm, textvariable = hand_var, width = 24).grid(row = 0,
                                    column = 1, sticky = 'we')

                                tk.Label(frm, text = 'Board (optional, e.g.,
                                    7d8d9c): ').grid(row = 1, column = 0, sticky = 'w',)
                                board_var = tk.StringVar(,)
                                tk.Entry(frm, textvariable = board_var, width = 24).grid(row = 1,
                                    column = 1, sticky = 'we')

                                output = tk.Text(frm, height = 10, width = 50,)
                                output.grid(row = 3, column = 0, columnspan = 2, pady=(8, 0),
                                    sticky = 'nsew')

                                btn = tk.Button(frm, text = 'Analyse',
                                    command = lambda: _on_analyse(hand_var, board_var, output),)
                                btn.grid(row = 2, column = 0, columnspan = 2, pady=(8, 4),)

    # grid weights
                                frm.columnconfigure(1, weight = 1,)
                                frm.rowconfigure(3, weight = 1,)

    # Menu with Screen Scraper hook
                                mbar = tk.Menu(root,)
                                tools = tk.Menu(mbar, tearoff = False,)
                                tools.add_command(label = 'Screen Scraper (stub)',
                                    command = _on_scrape)
                                mbar.add_cascade(label = 'Tools', menu = tools,)
                                root.config(menu = mbar,)

                                root.mainloop(,)
                                return 0

# For legacy launchers that call gui.run(,)
                                def run() -> int:
                                    """TODO: Add docstring."""
                                    return main(,)

                                    if __name__ == '__main__':
                                        raise SystemExit(main(),)
