# Release Notes - PokerTool v38.0.0

## 🎉 Comprehensive Hand History System

**Release Date:** 2025-10-12
**Branch:** release/v38.0.0
**Tag:** v38.0.0

---

## 🚀 Major Features

### Hand History Tracking & Display
A complete system for recording, storing, and analyzing every hand played:

- **SQLite Database Backend** - Persistent storage in `hand_history.db`
- **Real-time Statistics** - Win rate, total net, average pot size
- **Detailed Hand Records** - Players, positions, cards, actions, results
- **Advanced Filtering** - By hero, table, or result
- **JSON Export** - Export hands for external analysis
- **Beautiful GUI Tab** - Integrated "📚 History" tab with modern UI

---

## 📊 What Gets Tracked

### Per Hand:

- **Unique Hand ID** - Timestamp-based identifier
- **Table & Site** - Table name and poker site
- **Blinds** - Small blind / big blind amounts
- **Players** - All seats with positions (BTN, SB, BB, etc.)
- **Stack Sizes** - Starting and ending stacks
- **Cards** - Hero cards and board cards
- **Actions** - Complete betting sequence by stage
- **Pot Size** - Final pot amount
- **Winners** - Who won and how much
- **Hero Performance** - Win/loss/push with net amount
- **Duration** - How long the hand took

### Statistics:

- Total hands played
- Hands won / lost
- Win rate percentage
- Total net profit/loss
- Average pot size
- Max pot size won

---

## 🎨 GUI Features

### Statistics Dashboard
6 key metrics displayed prominently:

- Total Hands
- Hands Won
- Hands Lost
- Win Rate %
- Total Net ($)
- Average Pot Size ($)

### Filter & Sort

- Filter by hero name
- Filter by table name
- Filter by result (Won/Lost/Pushed)
- Sort by any column (click header)

### Hand Table View
9-column table showing:

- Time (timestamp)
- Table name
- Hero name
- Position (BTN/SB/BB/etc)
- Result (✓/✗/=)
- Pot size
- Net amount
- Final stage (preflop/flop/turn/river)
- Number of players

Color-coded rows:

- 🟢 Green background = Win
- 🔴 Red background = Loss
- ⚪ White background = Push

### Detail Pane
Click any hand to see complete details:

- Hand ID and metadata
- All players with seats and positions
- Hero cards (highlighted)
- Board cards
- Complete action sequence
- Winners and results

### Actions

- 🔄 **Refresh** - Reload from database
- 💾 **Export** - Save to JSON file
- 🗑️ **Clear All** - Delete all history (with confirmation)

---

## 🔧 Technical Architecture

### Data Model

**HandHistory:**
```python
hand_id: str
timestamp: str  # ISO format
table_name: str
site: str
small_blind: float
big_blind: float
players: List[PlayerInfo]
hero_cards: List[str]
board_cards: List[str]
actions: List[PlayerAction]
pot_size: float
winners: List[str]
hero_result: str  # "won"/"lost"/"pushed"
hero_net: float
final_stage: GameStage
duration_seconds: float
```

**PlayerInfo:**
```python
seat_number: int
player_name: str
starting_stack: float
ending_stack: float
position: str  # "BTN", "SB", "BB", etc.
is_hero: bool
cards: List[str]  # ["As", "Kh"]
won_amount: float
```

**PlayerAction:**
```python
player_name: str
action_type: ActionType  # fold/check/call/bet/raise/all_in
amount: float
stage: GameStage  # preflop/flop/turn/river
timestamp: str
```

### Database Schema

**Table: hands**

- hand_id (PRIMARY KEY)
- timestamp (INDEXED)
- table_name (INDEXED)
- site
- small_blind, big_blind
- pot_size
- hero_name (INDEXED)
- hero_result
- hero_net
- final_stage
- duration_seconds
- hand_data (JSON)
- created_at

### Files Added

**src/pokertool/hand_history_db.py** (550 lines)

- `HandHistory`, `PlayerInfo`, `PlayerAction` dataclasses
- `HandHistoryDatabase` class with full CRUD
- Statistics aggregation methods
- JSON serialization/deserialization
- Global singleton: `get_hand_history_db()`

**src/pokertool/enhanced_gui_components/tabs/hand_history_tab.py** (610 lines)

- `HandHistoryTabMixin` for GUI integration
- Complete tab builder with all UI components
- Event handlers for filtering, sorting, selection
- Export and clear functionality

**Modified Files:**

- **src/pokertool/enhanced_gui.py** - Added HandHistoryTabMixin inheritance
- **src/pokertool/enhanced_gui_components/tabs/__init__.py** - Added HandHistoryTabMixin export

---

## 📈 Accuracy Focus

### Position Tracking

- Accurate seat-to-position mapping
- Dealer button tracking
- Automatic SB/BB assignment based on button
- Position labels: BTN, SB, BB, UTG, MP, CO, etc.

### Stack & Pot Calculations

- Precise starting/ending stack amounts
- Accurate pot size calculation
- Net win/loss per player
- Hero-specific P&L tracking

### Action Sequencing

- Complete betting history by street
- Timestamp for each action
- Amount tracking for all bets/raises
- Proper action type classification

### Card Recording

- Hero hole cards preserved
- Board cards by street
- Showdown hands (when available)

---

## 🎯 Use Cases

### Session Analysis

- Review all hands from a session
- Calculate session P&L
- Identify profitable/losing patterns
- Track performance over time

### Hand Review

- Study specific hands in detail
- Analyze betting sequences
- Review decision points
- Learn from mistakes

### Statistics Tracking

- Win rate by position
- Average pot size by stakes
- Net profit over time
- Hands played per session

### Export & Share

- Export hands to JSON
- Share interesting hands
- Import to analysis tools
- Backup hand history

---

## 🔜 Future Enhancements

Ready for:

- **Hand Replayer** - Visual playback of hands
- **Advanced Stats** - VPIP, PFR, 3-bet%, aggression factor
- **Tournament Tracking** - Separate tournament vs cash game stats
- **Session Analysis** - Group hands by session
- **Equity Calculator** - Integrate hand ranges and equity
- **HUD Integration** - Display stats during play
- **Hand Import** - Import from other poker sites
- **Range Analysis** - Track opponent tendencies

---

## 📦 Installation

The HandHistory system is included in v38.0.0 and requires no additional setup.

**Database file:** `hand_history.db` (auto-created in project root)
**Note:** The database file is gitignored to protect privacy

---

## 🐛 Known Issues

None reported at release time.

---

## 🔒 Privacy & Data

- All hand history data stored **locally only**
- Database file is gitignored (not tracked)
- No data transmitted to external servers
- Export is opt-in only

---

## 📝 Version History

- **v38.0.0** (2025-10-12) - Complete Hand History system
- **v37.0.0** (2025-10-12) - Poker handle configuration & OpenCV fix
- **v36.0.0** (2025-10-12) - Purple table detection & startup validation
- **v35.0.0** (2025-10-12) - Confidence-aware decision API
- **v34.0.0** (2025-10-12) - Enhanced UX with hero position

---

## 🙏 Credits

- **Architecture & Implementation:** Claude Code
- **Database Design:** SQLite with indexed queries
- **GUI Design:** tkinter with custom styling
- **Testing:** Comprehensive validation of all features

---

## 📞 Support

Having issues? Check:

1. Is `hand_history.db` being created in the project root?
2. Do you have write permissions in the project directory?
3. Are you seeing the "📚 History" tab in the GUI?
4. Try clicking "🔄 Refresh" to reload data

---

**Enjoy comprehensive hand tracking with PokerTool v38.0.0!** 🎰📊
