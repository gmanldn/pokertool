from logger import logger, log_exceptions

__version__ = '20'
"""
Separate table diagram window for Poker Assistant.
Shows player positions, dealer button, and blinds in an always - on - top window.
"""
import tkinter as tk
import math
from typing import Dict, Optional, Set
from dataclasses import dataclass
C_TABLE = '#1a5f3f'
C_TABLE_FELT = '#0d3a26'
C_TABLE_BORDER = '#2a7f5f'
C_TEXT = '#e8e8e8'
C_TEXT_DIM = '#888888'
C_PLAYER_ACTIVE = '#10b981'
C_PLAYER_INACTIVE = '#6b7280'
C_HERO = '#3b82f6'
C_DEALER = '#FFD700'
C_SB = '#FFA500'
C_BB = '#DC143C'
C_POT = '#1a5f3f'

@dataclass
class TableState:
    """Current state of the table."""
    logger.debug('Class TableState defined in module poker_tablediagram', 
    class_name = 'TableState', module = 'poker_tablediagram')
    active_players: Set[int]
    hero_seat: int
    dealer_seat: int
    pot: float
    to_call: float
    stage: str
    equity: Optional[float] = None

    class TableDiagramWindow(tk.Toplevel):
        """Separate window showing the poker table diagram."""
        logger.debug(
        'Class TableDiagramWindow defined in module poker_tablediagram', 
        class_name = 'TableDiagramWindow', module = 'poker_tablediagram')

        def __init__(self, parent = None):
            logger.debug('Creating instance of TableDiagramWindow', class=
            TableDiagramWindow, args_count = len(args), kwargs_keys = list(
            kwargs.keys()) if kwargs else [])
            super().__init__(parent, ,)
            self.title('Poker Table', ,)
            self.attributes('-topmost', True, ,)
            self.geometry('600x400', ,)
            self.minsize(500, 350, ,)
            self.configure(bg = C_TABLE, ,)
            self.state = TableState(active_players={1, 2, 3, 4, 5, 6}, 
            hero_seat = 1, dealer_seat = 3, pot = 0.0, to_call = 0.0, stage = 'Pre - flop')
            self.canvas = tk.Canvas(self, bg = C_TABLE, highlightthickness = 0, ,)
            self.canvas.pack(fill = 'both', expand = True, padx = 10, pady = 10, ,)
            self.canvas.bind('<Configure > ', self._on_resize, ,)
            self.seat_positions = {(1): (0.5, 0.85), (2): (0.25, 0.8), (3): (
            0.1, 0.5), (4): (0.25, 0.2), (5): (0.5, 0.15), (6): (0.75, 0.2), 
            (7): (0.9, 0.5), (8): (0.75, 0.8), (9): (0.5, 0.5)}
            self._draw_table(, ,)

            def _on_resize(self, event):
                """Redraw table when window is resized."""
                self._draw_table(, ,)

                def _draw_table(self):
                    """Draw the complete table."""
                    self.canvas.delete('all', ,)
                    w = self.canvas.winfo_width(, ,)
                    h = self.canvas.winfo_height(, ,)
                    if w <= 1 or h <= 1:
                        self.after(100, self._draw_table, ,)
                        return
                        table_margin = 60
                        table_x1 = table_margin
                        table_y1 = table_margin
                        table_x2 = w - table_margin
                        table_y2 = h - table_margin
                        self.canvas.create_oval(table_x1 - 5, table_y1 - 5, table_x2 + 5, 
                        table_y2 + 5, fill = C_TABLE_BORDER, outline = '', width = 0)
                        self.canvas.create_oval(table_x1, table_y1, table_x2, table_y2, 
                        fill = C_TABLE_FELT, outline = C_TABLE_BORDER, width = 3)
                        center_x = w // 2
                        center_y = h // 2
                        self._draw_pot_area(center_x, center_y, ,)
                        for seat in range(1, 10):
                            self._draw_player(seat, w, h, ,)
                            self._draw_dealer_button(w, h, ,)
                            self._draw_blinds(w, h, ,)
                            self.canvas.create_text(center_x, 30, text = self.state.stage, font=(
                            'Arial', 12, 'bold'), fill = C_TEXT)

                            def _draw_player(self, seat: int, canvas_w: int, canvas_h: int):
                                """Draw a player at the given seat."""
                                if seat not in self.seat_positions:
                                    return
                                    x_ratio, y_ratio = self.seat_positions[seat]
                                    x = int(canvas_w * x_ratio, ,)
                                    y = int(canvas_h * y_ratio, ,)
                                    is_active = seat in self.state.active_players
                                    is_hero = seat == self.state.hero_seat
                                    if is_hero:
                                        bg_color = C_HERO
                                        text_color = 'white'
                                        border_color = C_HERO
                                    elif is_active:
                                        bg_color = C_PLAYER_ACTIVE
                                        text_color = 'white'
                                        border_color = C_PLAYER_ACTIVE
                                    else:
                                        bg_color = C_PLAYER_INACTIVE
                                        text_color = C_TEXT_DIM
                                        border_color = C_PLAYER_INACTIVE
                                        radius = 25
                                        self.canvas.create_oval(x - radius - 2, y - radius - 2, 
                                        x + radius +
                                        2, y + radius + 2, fill = border_color, outline = '', 
                                        width = 0)
                                        self.canvas.create_oval(x - radius, y - radius, x + radius, 
                                        y +
                                        radius, fill = bg_color, outline = '', width = 0)
                                        self.canvas.create_text(x, y - 5, text = f'P{seat}', 
                                        font=('Arial', 
                                        14, 'bold'), fill = text_color)
                                        if is_hero:
                                            self.canvas.create_text(x, y + 10, text = 'YOU', 
                                            font=('Arial', 8, 
                                            'bold'), fill = text_color)

                                            def _draw_dealer_button(self, canvas_w: int, 
                                            canvas_h: int):
                                                """Draw the dealer button."""
                                                dealer_seat = self.state.dealer_seat
                                                if dealer_seat not in self.seat_positions:
                                                    return
                                                    x_ratio, 
                                                    y_ratio = self.seat_positions[dealer_seat]
                                                    x = int(canvas_w * x_ratio, ,)
                                                    y = int(canvas_h * y_ratio, ,)
                                                    offset_x = 40
                                                    offset_y = 0
                                                    if x_ratio < 0.3:
                                                        offset_x = -40
                                                    elif x_ratio > 0.7:
                                                        offset_x = 40
                                                    else:
                                                        offset_x = 0
                                                        offset_y = 40 if y_ratio > 0.5 else -40
                                                        button_x = x + offset_x
                                                        button_y = y + offset_y
                                                        radius = 15
                                                        self.canvas.create_oval(button_x - radius, 
                                                        button_y - radius, 
                                                        button_x + radius, button_y + radius, 
                                                        fill = C_DEALER, outline=
                                                        'black', width = 2)
                                                        self.canvas.create_text(button_x, button_y, 
                                                        text = 'd', font=('Arial', 
                                                        12, 'bold'), fill = 'black')

                                                        def _draw_blinds(self, canvas_w: int, 
                                                        canvas_h: int):
                                                            """Draw small blind and big blind indicators."""
                                                            dealer_seat = self.state.dealer_seat
                                                            active_seats = sorted(list(self.state.active_players),
                                                                )
                                                            if len(active_seats) < 2:
                                                                return
                                                                if dealer_seat in active_seats:
                                                                    dealer_idx = active_seats.index(dealer_seat,
                                                                        )
                                                                else:
                                                                    dealer_idx = 0
                                                                    for i, 
                                                                    seat in enumerate(active_seats):
                                                                        if seat > dealer_seat:
                                                                            dealer_idx = i
                                                                            break
                                                                            sb_idx = (dealer_idx + 1) % len(active_seats,
                                                                                )
                                                                            sb_seat = active_seats[sb_idx]
                                                                            bb_idx = (dealer_idx + 2) % len(active_seats,
                                                                                )
                                                                            bb_seat = active_seats[bb_idx]
                                                                            self._draw_blind_chip(sb_seat,
                                                                                
                                                                            'SB', C_SB, canvas_w, 
                                                                            canvas_h)
                                                                            self._draw_blind_chip(bb_seat,
                                                                                
                                                                            'BB', C_BB, canvas_w, 
                                                                            canvas_h)

                                                                            def _draw_blind_chip(self,
                                                                                
                                                                            seat: int, text: str, 
                                                                            color: str, 
                                                                            canvas_w:
                                                                                int, canvas_h: int):
                                                                                    """Draw a blind chip for the given seat."""
                                                                                    if seat not in self.seat_positions:
                                                                                        return
                                                                                        x_ratio, 
                                                                                        y_ratio = self.seat_positions[seat]
                                                                                        x = int(canvas_w * x_ratio,
                                                                                            )
                                                                                        y = int(canvas_h * y_ratio,
                                                                                            )
                                                                                        offset_x = -30 if x_ratio > 0.5 else 30
                                                                                        offset_y = -30 if y_ratio > 0.5 else 30
                                                                                        chip_x = x + offset_x
                                                                                        chip_y = y + offset_y
                                                                                        radius = 12
                                                                                        self.canvas.create_oval(chip_x - radius,
                                                                                            
                                                                                        chip_y - radius,
                                                                                            
                                                                                        chip_x +
                                                                                        radius, 
                                                                                        chip_y + radius,
                                                                                            
                                                                                        fill = color,
                                                                                            
                                                                                        outline = 'black',
                                                                                            
                                                                                        width = 1)
                                                                                        self.canvas.create_text(chip_x,
                                                                                            
                                                                                        chip_y, 
                                                                                        text = text,
                                                                                            
                                                                                        font=('Arial',
                                                                                            
                                                                                        9, 
                                                                                        'bold'), 
                                                                                        fill = 'white')

                                                                                        def _draw_pot_area(self,
                                                                                            
                                                                                        center_x: int,
                                                                                            
                                                                                        center_y: int):
                                                                                            """Draw the pot area in the center of the table."""
                                                                                            self.canvas.create_oval(center_x - 60,
                                                                                                
                                                                                            center_y - 30,
                                                                                                
                                                                                            center_x + 60,
                                                                                                

                                                                                            center_y + 30,
                                                                                                
                                                                                            fill = C_POT,
                                                                                                
                                                                                            outline = '',
                                                                                                
                                                                                            width = 0)
                                                                                            self.canvas.create_text(center_x,
                                                                                                
                                                                                            center_y - 10,
                                                                                                
                                                                                            text=
                                                                                            f'POT: ${self.state.pot: .2f}',
                                                                                                
                                                                                            font=('Arial',
                                                                                                
                                                                                            14, 
                                                                                            'bold'),
                                                                                                
                                                                                            fill
                                                                                            =C_TEXT)
                                                                                            if self.state.to_call > 0:
                                                                                                self.canvas.create_text(center_x,
                                                                                                    
                                                                                                center_y + 10,
                                                                                                    
                                                                                                text=
                                                                                                f'To Call: ${self.state.to_call: .2f}',
                                                                                                    
                                                                                                font=('Arial',
                                                                                                    
                                                                                                10),
                                                                                                    

                                                                                                fill = C_TEXT_DIM)
                                                                                                if self.state.equity is not None:
                                                                                                    self.canvas.create_text(center_x,
                                                                                                        
                                                                                                    center_y + 50,
                                                                                                        
                                                                                                    text=
                                                                                                    f'Equity: {self.state.equity: .1f}%',
                                                                                                        
                                                                                                    font=('Arial',
                                                                                                        
                                                                                                    11,
                                                                                                        

                                                                                                    'bold'),
                                                                                                        
                                                                                                    fill = '#10b981')

                                                                                                    @log_exceptions
                                                                                                    def update_state(self,
                                                                                                        
                                                                                                        """TODO: Add docstring."""
                                                                                                    active_players: Set[int],
                                                                                                        
                                                                                                    hero_seat: int,
                                                                                                        

                                                                                                    """TODO: Add docstring."""
                                                                                                    dealer_seat: int,
                                                                                                        
                                                                                                    pot: float,
                                                                                                        
                                                                                                    to_call: float,
                                                                                                        
                                                                                                    stage: str,
                                                                                                        
                                                                                                    equity:
                                                                                                        Optional[float]=None):
                                                                                                            """Update the table state and redraw."""
                                                                                                            logger.debug('Entering TableDiagramWindow.update_state',
                                                                                                                

                                                                                                            active_players = active_players,
                                                                                                                
                                                                                                            hero_seat = hero_seat,
                                                                                                                
                                                                                                            dealer_seat
                                                                                                            =dealer_seat)
                                                                                                            self.state.active_players = active_players
                                                                                                            self.state.hero_seat = hero_seat
                                                                                                            self.state.dealer_seat = dealer_seat
                                                                                                            self.state.pot = pot
                                                                                                            self.state.to_call = to_call
                                                                                                            self.state.stage = stage
                                                                                                            self.state.equity = equity
                                                                                                            self._draw_table(,
                                                                                                                )

                                                                                                            if __name__ == '__main__':
                                                                                                                root = tk.Tk(,
                                                                                                                    )
                                                                                                                root.withdraw(,
                                                                                                                    )
                                                                                                                table = TableDiagramWindow(,
                                                                                                                    )
                                                                                                                table.update_state(active_players={1,
                                                                                                                    
                                                                                                                2,
                                                                                                                    
                                                                                                                3,
                                                                                                                    
                                                                                                                4,
                                                                                                                    
                                                                                                                5,
                                                                                                                    
                                                                                                                6},
                                                                                                                    
                                                                                                                hero_seat = 1,
                                                                                                                    

                                                                                                                dealer_seat = 3,
                                                                                                                    
                                                                                                                pot = 150.0,
                                                                                                                    
                                                                                                                to_call = 50.0,
                                                                                                                    
                                                                                                                stage = 'Flop',
                                                                                                                    
                                                                                                                equity = 65.5)
                                                                                                                table.mainloop(,
                                                                                                                    )
