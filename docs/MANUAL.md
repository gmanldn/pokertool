# PokerTool Comprehensive Manual Outline

> Operational Note: Track new work with `python new_task.py`, which records GUID-stamped issues inside `docs/TODO.md`. Manual backlog edits are prohibited; legacy tasks moved to `docs/TODO_ARCHIVE.md`.

## Overview and Introduction

- Purpose and Scope: Begin with a clear introduction to PokerTool – a
  single-player poker assistant for Texas Hold’em. Explain that it helps
  users practice and analyze hands by calculating win probabilities and
  giving advice in real-time. Mention the target audience (poker
  enthusiasts or learners) and how the tool is intended for training and
  analysis, not real gambling.

- **Key Features Summary:** Provide a brief summary of the main
  features: an interactive card selection GUI, on-the-fly win
  probability calculation, strategic advice, hand result logging, and
  statistical review of past hands. This gives readers a high-level
  preview of what the tool offers.

- **Technology and Version:** Note that PokerTool is written in Python
  (requires Python 3.8+) and uses a Tkinter graphical interface with an
  SQLite database for storing data via SQLAlchemy. State the current
  version (e.g. *PokerTool v1.0.0*) and any relevant background or
  motivation for the project.

## Features and Functionality (User Guide)

- Card Selection and Table Setup: Explain how users interact with the
  card deck and table settings in the GUI:

  - The full **deck of 52 cards** is displayed, organized by suit
    (♠♥♦♣). Users can select their **hole cards** by dragging and
    dropping cards onto the designated slots or by double-clicking a
    card to auto-fill the next available position.

  - Describe the **“Your Hole Cards”** section (two slots)
    and **“Community Cards”** section (five slots for flop, turn,
    river). Each slot is labeled (e.g., “Flop 1”, “Turn”, etc.) and
    accepts a dropped card. Illustrate how the interface highlights
    these drop zones (e.g., “Drop Card Here” placeholders) and how cards
    become grayed out in the deck once used.

  - Detail the **table position selector** (spinbox 1-6) which lets the
    user indicate their seat relative to the dealer button, and
    the **number of opponents selector** (spinbox 1-9) to simulate
    different table sizes. Explain that these inputs factor into the
    advice given (position can affect strategy, and more opponents
    generally lower win probability).

  - Mention the **chip stack size** dropdown (low/medium/high). Clarify
    that while this doesn’t affect the probability calculation, it is
    recorded with each hand for context. It allows the user to note
    whether they were short-stacked or deep-stacked, which might
    influence decision-making.

- **Win Probability Calculation & Advice:** Describe how the tool
  provides real-time odds and suggestions:

  - As soon as two hole cards are set (and whenever community cards or
    opponent count change), the **win probability** is calculated and
    displayed as a percentage. Explain in simple terms that PokerTool
    uses a **heuristic algorithm** (based on hand strength and basic
    combinations) to estimate the chance of winning the hand. For
    example, a **pocket pair** or high-ranking cards yield higher base
    odds, while suited cards get a bonus, and potential combinations on
    the board (pairs, flush draws) are accounted for in a rudimentary
    way. The probability is adjusted down for more opponents and bounded
    between 5% and 95% to avoid extremes.

  - The calculated probability is prominently shown (e.g. in large font,
    blue text by default). Alongside it, the tool provides **advice
    text** that changes according to the probability range: if the win
    chance is very high (e.g. \>70%), it might say “Strong hand!
    Consider betting/raising” (often shown in green); for decent odds
    (\>50%) maybe “Good hand, play cautiously” (blue); for middling odds
    (\>30%) “Marginal hand, consider your position” (orange); and for
    low odds “Weak hand, consider folding” (red). Describe each advice
    category and how the color-coding gives a quick visual cue to the
    user about the hand’s strength.

  - Emphasize that this is a **simplified odds calculator** – it
    does *not* run a full simulation but provides a quick estimate. The
    manual should encourage users to use the advice as a general
    guideline, combined with their own judgment.

- **Action Buttons – Clearing and Recording Hands:** Outline the
  functions of the action buttons below the cards area:

  - **Clear All Cards:** This button resets the table. When clicked, it
    removes any cards from the hole and community slots, re-enables all
    cards in the deck (so they can be chosen again), and resets the win
    probability display to a default state (e.g., “--” or 0.0%). This
    allows the user to start analyzing a new hand quickly.

  - **Record Win/Loss/Tie:** These three buttons let the user log the
    outcome of the current hand scenario after they finish a real hand
    in play. Explain that to record a result, the user must have exactly
    2 hole cards selected (the tool will warn if not). The user then
    chooses the appropriate outcome: **Win**, **Loss**, or **Tie**. Once
    clicked, the tool will save the hand’s data (hole cards, any
    community cards, position, number of opponents, chip stack state,
    and the predicted win probability) into its history database, marked
    with the selected result. A confirmation message is shown (“Hand
    recorded as win/lose/tie”), and the interface is cleared for a new
    hand. This feature is useful for tracking performance and comparing
    predicted odds with actual outcomes over time.

- **Hand History Review (Statistics Menu):** Describe the feature that
  lets users review their logged hands and overall performance:

  - In the menu bar, the **“Statistics”** menu contains an option
    for **“Hand History”**. Selecting this opens a dedicated History
    window (titled “Hand History”) showing a list of all recorded hands
    in a table format. Explain the columns displayed: position, hole
    cards, community cards, predicted win percentage, actual result,
    etc., providing an overview of what each column means. Each row
    corresponds to one recorded hand, and they are typically sorted by
    most recent first.

  - Point out that at the bottom or top of the history window,
    some **summary statistics** are shown – for example, the total
    number of hands recorded, how many of those were wins, and the
    overall win rate (percentage of hands won). This gives the user a
    simple way to gauge their success and perhaps the accuracy of the
    tool’s predictions over a set of hands.

  - If applicable, mention that the history view may allow scrolling or
    filtering (depending on implementation) and that it’s read-only
    (users cannot edit past records through the GUI). The purpose is to
    reflect on past decisions and outcomes.

  - Also note the **“Clear History”** function (also under the
    Statistics menu). When selected, it will prompt the user for
    confirmation (“Are you sure you want to clear all hand history?”).
    Upon confirmation, *all* recorded hand entries will be deleted from
    the database, and a success message will confirm the history was
    cleared. This can be used if the user wants to reset their stats or
    if the database grows too large.

- **User Experience and Workflow:** After detailing individual features,
  provide a brief walkthrough of a typical use-case scenario to tie it
  all together. For example: “**Using PokerTool:** The user starts the
  application, selects their two hole cards (either by drag-and-drop or
  double-click). The win probability and advice update immediately,
  helping the user decide how to play. The user can adjust the number of
  opponents or add community cards (as the flop/turn/river are revealed
  in a real game) to see how the odds and advice change. After the hand
  is complete, the user clicks ‘Record Win’ (if they won, for instance)
  to log the hand. Later, they might review their hand history via the
  menu to analyze how often they win with certain cards or how their
  decisions align with the tool’s suggestions.” This narrative will help
  readers understand the flow and encourage them to use all the features
  in context.

## Technical Deep-Dive (Developer Guide by Module)

In this section, provide an in-depth explanation of the codebase for
  developers or advanced users. Go module by module, describing the
  purpose of each and highlighting important classes, functions, and
  design decisions. Include references to code comments and definitions
  for clarity.

- **Module: **poker_main.py** (GUI and Application Controller)** – This
  module contains the main application logic tying together the UI and
  the game functionality. Key components to document:

  - *PokerAssistant class:* Explain that this is the primary class
    representing the application’s GUI. It manages all UI elements and
    state. Cover the **constructor** (\_\_init\_\_): it initializes the
    Tkinter root window, creates an instance of a full card deck, and
    sets up variables to track game state (such
    as position, num_opponents, chip_stack as Tkinter variables, and
    lists for hole_cards and community_cards). It then calls an
    internal \_setup_ui() method to build the interface and finally
    triggers an initial probability update. Emphasize how the session
    context (a database session generator) is passed in and stored
    as self.session_context for later database operations.

  - *UI Layout Methods:* Detail how the UI is constructed through helper
    methods that PokerAssistant defines. For
    instance: \_setup_ui() orchestrates the creation of sub-components
    (card deck area, controls, card slots, displays, buttons, menu).
    Each of those has its own method:

    - \_create_card_deck(parent): Lays out the grid of card buttons
      representing the deck. Describe how each card is a
      Tkinter Button labeled with rank and suit, color-coded (red for
      hearts/diamonds, black for spades/clubs). Explain that each button
      is bound to events: a single click to start dragging that card and
      a double-click to auto-place the card into the next available
      slot. Mention how the code creates a Card object for each button
      and stores the Button in a dictionary for easy enabling/disabling
      by card identifier.

    - \_create_position_controls(parent): Creates spinboxes for table
      position and opponents, and a combobox for chip stack selection.
      Note how changes in these controls
      trigger \_update_probability() (for instance, binding the
      Return/Enter key to recalc odds when a value is entered).

    - \_create_hole_cards_area(parent) and \_create_community_area(parent):
      Set up labeled frames with empty label widgets where cards will be
      dropped. Explain how each label is initialized with placeholder
      text and a sunken border to indicate a drop target. Each label is
      bound to a click event that finalizes dropping a card in that slot
      (\_drop_hole_card or \_drop_community_card handlers). The design
      uses two hole card slots and five community card slots aligned in
      a row.

    - \_create_probability_display(parent): Sets up the large label for
      displaying the win probability and a smaller label for advice
      text. Mention font sizes and styling (e.g., big bold percentage,
      colored advice text) to show developers how the UI feedback is
      presented.

    - \_create_action_buttons(parent): Creates the buttons for “Clear
      All Cards” and “Record Win/Loss/Tie” actions and binds them to
      their respective methods. Note that the Record buttons use lambda
      to pass the result string to \_record_result.

    - \_create_menu(): Builds the top menu bar, particularly
      the **Statistics** menu. Explain that it iterates through
      a PLUGIN_REGISTRY of plugins to add each as a menu item under
      “Statistics”. By default, this means “Hand History” and “Clear
      History” menu options will appear, and selecting one will
      invoke \_run_plugin with the plugin’s name. This design allows
      easy extension of the menu via plugins.

  - *Event Handling and Card Management:* Describe the methods that
    handle user interactions with cards:

    - \_start_drag(card): Called when a deck card button is clicked,
      this method marks the selected card as the one being dragged
      (stored in self.dragging_card), but only if that card isn’t
      already in play. This prepares the application to drop the card
      into a slot.

    - \_drop_hole_card(index) and \_drop_community_card(index): Called
      when the user clicks on a hole or community slot while a card is
      “in hand”. These methods place the dragged card into the
      appropriate list (hole_cards or community_cards) at the given
      index if that slot is free. They then call helper functions to
      update the state: \_update_next_position() (to track how many
      cards are filled), \_update_card_displays() (to redraw the card
      images/text in the UI slots), \_disable_card_button(card) (to gray
      out the card in the deck so it can’t be reused), and
      finally \_update_probability() to recalc odds with the new card in
      play. After dropping, self.dragging_card is cleared.

    - \_auto_fill_card(card): This is triggered by double-clicking a
      card in the deck. It automatically places the card into the next
      available position in the sequence of hole and community cards.
      Explain the logic: fill two hole cards first, then up to five
      community cards, in order. If all slots are full, it shows a
      warning (hand complete). After placing the card, it similarly
      updates displays and probability.

    - \_clear_all_cards(): Resets the table state when the user clicks
      the “Clear All Cards” button. Document how it re-enables all deck
      buttons (iterating through both hole and community cards to
      call \_enable_card_button on each), clears
      the hole_cards and community_cards lists, resets the next position
      counter, and updates all the slot labels back to their default
      "Drop Card Here" or slot name text and background colors. Finally,
      it calls \_update_probability() which will detect no hole cards
      and thus display “--” and a prompt to start by adding hole cards.
      This method effectively starts a fresh hand scenario.

  - *Probability Update and Advice:* Explain the implementation
    of \_update_probability() which is central to the tool’s
    functionality. It checks if there are 2 hole cards selected; if so,
    it calls the calculate_win_probability function (imported from
    poker_modules) with the current hole, community cards, and number of
    opponents. The returned probability (0.0 to 0.95 range) is then
    displayed as a percentage on the GUI. Next, the method determines
    which advice message to show based on thresholds (e.g., \>70%,
    \>50%, \>30%, or else) and updates the advice_label text and color
    accordingly. If there aren’t yet two hole cards, it will display
    “--” and prompt the user to add hole cards. Developers should
    understand how this function connects the backend odds calculation
    with the frontend display logic.

  - *Recording Results:* Describe the \_record_result(result:
    str) method, which handles logging a hand to the database when the
    user clicks one of the record buttons. It first validates that
    exactly two hole cards are present (showing a warning if not). Then
    inside a with self.session_context() as session: block, it creates a
    new HandHistory object (from the ORM model) with details of the
    hand: the position, a concatenated string of the two hole cards, a
    space-separated string of community cards (if any) or None, the
    current win probability, the actual result (win/lose/tie passed in),
    and the chip stack selection. It adds this to the session and
    commits the transaction to save it. If successful, a confirmation
    dialog is shown to the user and \_clear_all_cards() is called to
    reset for the next hand. If there’s an error during save, it catches
    the exception and shows an error dialog. In the manual, note how the
    design separates the GUI from direct database access by using
    the session_context for ORM operations, which keeps things modular
    and testable.

  - *Plugin System Integration:* Explain how external or optional
    features are integrated via the \_run_plugin(name: str) method and
    the menu. \_run_plugin looks up the plugin function by name in
    the PLUGIN_REGISTRY (discussed later) and calls it,
    passing self (the PokerAssistant instance) as an argument. It wraps
    the call in a try/except to catch any errors in the plugin and show
    a message box error if one occurs. This mechanism allows adding new
    functionality without modifying the main GUI code – as long as a
    function is registered in the registry, it will appear in the menu
    and can perform an action using the running PokerAssistant (for
    example, opening the history window or clearing data). Document how
    the included plugins (“Hand History” and “Clear History”) are
    triggered through this system when the user selects them from the
    menu.

  - *Application Entry Point:* Highlight the run(engine,
    session_context) function at the bottom of poker_main.py. This is a
    convenience function that initializes the Tkinter root window,
    creates a PokerAssistant, and starts the Tk event loop
    (root.mainloop()). Explain that when integrating the PokerTool, a
    developer would first set up the database engine and session context
    (as done in poker_init.py), then call poker_main.run(...) to launch
    the GUI. This separation allows the database setup to be done
    externally and passed in, making it easier to manage or test. If
    there are command-line interfaces or other ways to launch, mention
    those here as well.

- **Module: **poker_modules.py** (Core Logic and Models)** – This module
  provides the underlying data structures, algorithms, and a lightweight
  plugin architecture that support the PokerTool’s functionality. Key
  topics to cover:

  - *Card Representation:* Document the Card class, which represents a
    standard playing card with a rank and suit. It also computes a
    numeric value for the rank for easy comparison (based on an ordered
    list from 2 up to A) and defines \_\_str\_\_ and \_\_repr\_\_ for
    convenient display. Explain that ranks are defined
    as '2'–'9', 'T' (10), 'J', 'Q', 'K', 'A', and suits as ♠♥♦♣. Also
    mention the module-level constants SUITS, RANKS, and
    the RANK_VALUES mapping which are used to generate the full deck and
    evaluate hands.

  - *Deck Creation:* Describe the create_deck() function that returns a
    list of 52 Card instances (all combinations of the defined ranks and
    suits). Note that the GUI uses this to initialize available cards.
    If any shuffling or randomization is relevant, mention it (though in
    the current UI, the deck is laid out sorted by suit and rank, not
    shuffled, since it’s for selection rather than dealing random
    cards).

  - *Win Probability Algorithm:* Provide a clear explanation of
    the calculate_win_probability(hole_cards, community_cards,
    num_opponents=1) -\> float function. Break down its approach:

    - It expects exactly two hole cards; if not, it returns 0.0
      immediately (in practice, the UI ensures to only call this when
      two hole cards are present).

    - It computes a **base hand strength** starting at 0.0. If the hole
      cards form a **pair**, it adds a significant bonus (e.g., 0.3 plus
      a small factor per rank value). If not a pair, it adds a smaller
      base depending on the high card’s value, and gives a bonus if they
      are suited.

    - If community cards are provided (e.g., after flop/turn/river in a
      real scenario), the function does a very basic evaluation: it
      combines hole and community cards and checks for certain patterns.
      For example, it looks for any **pair or better** by counting ranks
      – for each rank that appears 2 or more times, it adds a bonus. It
      also checks for a **possible flush** by seeing if at least three
      cards share the same suit, adding a smaller bonus if so. (Note:
      The manual should clarify that this is a simplistic approach and
      does not cover all poker hand strengths like straights or full
      houses comprehensively.)

    - After adjusting for community cards, the function adjusts the
      probability for the number of opponents: essentially dividing the
      base strength by a factor that grows with each opponent (each
      opponent adds 0.3 to the divisor). This means more opponents
      reduce the win probability.

    - The result is clamped between 0.05 (5%) and 0.95 (95%) to avoid
      overly certain predictions. Explain why such clamping is used
      (never assume 100% certain win or absolute zero chance).

    - Mention that while this algorithm runs quickly and provides a
      rough estimate, it is not a full Monte Carlo simulation. It’s
      intended for quick feedback; developers or contributors could
      later improve this function for more accuracy.

    - If relevant, note how this function could be extended (for
      example, to consider straight draws, etc.) and that it’s a
      self-contained piece of logic that can be tested independently.

  - *ORM Data Models:* Discuss the basic database models defined in this
    module using SQLAlchemy’s declarative base (note:
    in poker_modules.py the Base is defined and used, but
    in poker_init.py a separate Base is also defined – address this
    discrepancy in the manual). Focus on those present
    in poker_modules.py:

    - **Player** model: A simple representation of a player with fields
      for id, name, and bankroll. In this version, it’s minimal (just a
      name and money). It ensures name is unique and indexed. Explain
      that the application seeds a default Player record (“You” with
      \$1000 bankroll) on first run. This might be used in future to
      support multiple players or persistent user profile.

    - **HandHistory** model: Stores each recorded hand’s outcome. List
      its columns: an auto-increment ID, timestamp (when the record was
      created), position (seat 1-6), hole_cards (stored as a string like
      "AsKh"), community_cards (string of cards or null if none),
      predicted_win_prob (the percentage at time of recording),
      actual_result (e.g., 'win'/'lose'/'tie'), and notes (which could
      be used for additional comments, though the UI doesn’t currently
      set this). Mention that the \_\_repr\_\_ is defined to print a
      concise summary of the hand. This table grows as the user records
      hands, and the Hand History plugin reads from here.

    - (Developers’ Note: The poker_init.py module redefines a more
      complex Player model and likely adds GameSession and Transaction
      models. It’s worth noting the difference: in poker_modules.py,
      these models are simpler and possibly deprecated in favor of those
      in poker_init.py. We will discuss the poker_init.py models
      separately. The manual should clarify which models are actively
      used by the running application. Likely, the application uses the
      models from poker_modules.py for HandHistory, because the plugin
      queries that. But it might use the more detailed Player
      from poker_init.py for extended stats. This is an area for careful
      explanation to avoid confusion.)

    - Explain the function seed_database(session) which checks if any
      Player exists, and if not, inserts the default player "You" with a
      starting bankroll of 1000. This ensures the database has at least
      one player profile. If an error occurs during seeding, it rolls
      back and raises a RuntimeError. Developers should run this at
      initialization so that the application always has a reference
      player record.

  - *Plugin Registry System:* This module implements a simple plugin
    architecture that the main GUI uses to populate the Statistics menu.
    Document the components:

    - PLUGIN_REGISTRY: a dictionary mapping plugin names (strings) to
      callable functions. When the app starts, this registry is empty,
      and plugin functions are added to it via a decorator.

    - @register_plugin(name): a decorator factory that returns a
      decorator function. When used above a function definition, it will
      register that function in the PLUGIN_REGISTRY under the given
      name. Explain how this works: if a plugin name is reused, it
      raises an error to avoid duplicates. This makes adding a new menu
      action as easy as writing a new function and tagging it
      with @register_plugin("Menu Label").

    - **Built-in Plugins:** Detail the two plugins provided by PokerTool
      out of the box:

      - *Hand History Plugin:* Registered as "Hand History". This plugin
        function opens the Hand History window described in the user
        features section. Walk through its implementation: it uses the
        controller (the PokerAssistant instance) passed in to create a
        new Toplevel window with a Treeview table. It fetches all
        HandHistory records from the database
        (using controller.session_context() and an SQLAlchemy query
        ordering by timestamp descending). It then populates the
        Treeview with each hand’s data (position, cards, etc.). After
        listing hands, it calculates win-rate statistics (counting wins
        vs total) and displays those in the window. This plugin
        showcases how to use the recorded data to provide useful
        insights to the user. It’s a reference for developers on how to
        read from the database and create new UI windows within the
        plugin system.

      - *Clear History Plugin:* Registered as "Clear History". This
        plugin deletes all records from the HandHistory table. Document
        its steps: it first asks the user to confirm the action via a
        yes/no message box. If confirmed, it obtains a database session
        and calls session.query(HandHistory).delete() to remove all
        entries, then commits the transaction. It wraps this in
        try/except to handle any exceptions (e.g., database locked or
        other errors) and shows an error message if something goes
        wrong. On success, it shows a message box indicating the history
        was cleared. This plugin demonstrates how to perform a write
        operation on the database through the plugin system.

    - Emphasize to developers that **creating a new plugin** is
      straightforward: define a function that takes
      the GameController (PokerAssistant) as an argument, perform
      whatever UI or data operations needed, and decorate it
      with @register_plugin("Name"). The new plugin will automatically
      appear in the Statistics menu next time the app runs, without
      additional wiring. This design makes PokerTool extensible for
      future features (for example, one could add a plugin to show
      graphs of win rate over time, or a tool to simulate opponent
      ranges, etc.).

- **Module: **poker_init.py** (Application Initialization and
  Configuration)** – This module is responsible for setting up the
  application’s environment, including the database connection and
  schema. It defines configuration constants and data models, some of
  which extend beyond the basic ones in poker_modules.py. Even if parts
  of this code are in development (since there is overlap in model
  definitions), the manual should cover the intent and usage of this
  module. Key points:

  - *Configuration Constants:* List and explain the important constants
    defined here, which configure the application’s behavior:

    - APP_NAME (e.g., "PokerTool") and APP_VERSION (e.g., 1.0.0) – the
      name and current version of the application. These might be used
      for display or in the database for migrations.

    - DATABASE_VERSION – an integer to track the schema version of the
      database. The manual should mention that if the app upgrades its
      database schema, this number is used to apply migrations.

    - MIN_PYTHON_VERSION – the minimum Python version required (3.8 in
      this case). This is enforced to ensure compatibility (for example,
      because of usage of certain features like typing annotations
      or walrus operator). The code likely
      checks sys.version_info against this and exits with a warning if
      not met.

    - DEFAULT_CHIP_STACK (e.g., 1000.0) – the starting bankroll for new
      players (and the value used in the Player model by default).

    - MAX_PLAYERS (e.g., 10) – possibly the maximum number of player
      profiles or seats the tool can handle. Not heavily used in the
      current single-user context, but noted for completeness.

    - BACKUP_RETENTION_DAYS (e.g., 30) – suggests that the tool might
      keep backups of the database or data for a certain number of days.
      Explain that if implemented, older data beyond this retention
      period might be pruned or archived. (The manual should clarify if
      this is a planned feature; if not active, it can be mentioned as a
      configurable constant for future use.)

  - *Database Engine Setup:* Describe how the application sets up the
    SQLite database using SQLAlchemy. It likely uses create_engine() to
    connect to a SQLite file (or memory) with appropriate options.
    Mention if the connection is set to
    use check_same_thread=False and StaticPool for thread safety with
    Tkinter (since GUI and DB might run in same process) – these details
    ensure the SQLite database can be accessed from different contexts
    (the plugins, etc.) without issues. Also note the use of event or
    other SQLAlchemy event hooks if any (for example, to enforce foreign
    keys in SQLite or to perform migrations). If the code uses an
    in-memory database for quick start, mention that and how data
    persistence is handled (maybe it copies to a file on exit or uses
    backup retention for file copies).

  - *Session Management:* Explain the use of sessionmaker and possibly
    a scoped_session to manage database sessions. The module likely
    defines a SessionLocal = sessionmaker(bind=engine) and a context
    manager @contextmanager def session_context(): yield
    SessionLocal() (or something similar) to provide
    the session_context function that poker_main passes to
    PokerAssistant. This design allows easy and safe transaction
    handling. Document this pattern for developers, as it’s crucial for
    understanding how database operations are done within GUI actions
    (each operation uses a fresh session and is committed or rolled back
    as needed).

  - *Extended ORM Models:* The poker_init.py module defines more
    comprehensive data models for a full poker tracking application.
    These include:

    - **Player (extended):** Unlike the simpler Player in poker_modules,
      this version includes many fields for tracking a player’s overall
      stats and info. List these fields: chip_stack (current money),
      total_winnings, total_losses, games_played, games_won, win_rate
      (as a property calculated on the fly), net_profit (property),
      avatar_path (for a profile image), notes (freeform text),
      skill_level (e.g., Beginner/Intermediate/etc.), created_at,
      updated_at timestamps, last_played date, and boolean is_active to
      mark if the player is currently active. The manual should explain
      that this richer model is designed to maintain a player’s history
      over time (e.g., how many games they played and won, how much
      money they’ve won or lost, etc.). Also, note the use of SQLAlchemy
      relationships: a Player has a one-to-many relationship
      with **GameSession** and **Transaction** records. This indicates
      the app can track individual game sessions for a player and
      financial transactions affecting their bankroll.

    - **GameSession:** Although the code snippet for GameSession isn’t
      fully visible, infer and describe its purpose. A GameSession
      likely represents a single poker session or game played by the
      user. It probably includes fields like an ID, a foreign key to
      Player, maybe a timestamp, duration, maybe outcome or profit for
      that session. Since Player.game_sessions is defined, a GameSession
      model exists linking back to Player (back_populates="player").
      Explain that this could be used to log each time the user sits
      down to play a series of hands, allowing aggregation of stats per
      session.

    - **Transaction:** Likewise, describe the intended Transaction
      model. Given Player.transactions relationship, a Transaction might
      log changes in a player’s bankroll (deposits, withdrawals,
      buy-ins, wins/losses in monetary terms). Fields likely include ID,
      player_id, amount, timestamp, type (e.g., “buy-in”, “payout”,
      “rebuy”, etc.). These records would enable a detailed financial
      history for the player.

    - **HandHistory (if redefined here):** It’s possible
      that poker_init.py either uses the same HandHistory
      from poker_modules or could have an expanded version. Clarify if
      HandHistory is defined in this module; if not, state that the
      application uses the definition from poker_modules.py for logging
      individual hands. (Consistency is important: the manual should
      point out if there are duplicate model definitions and which one
      is active. For the purpose of the manual, assume the develop
      branch is consolidating these models in poker_init.py for a
      unified database, and that going forward the extended models will
      be used.)

    - For each model, mention any unique constraints or indices (e.g.,
      unique player name, index on is_active in Player) and why they
      matter (unique names prevent duplicates, indexing active players
      could speed up queries).

    - Highlight the property methods, e.g., Player.win_rate and
      Player.net_profit, which automatically compute values from other
      fields. This is a nice feature of the data model to mention as it
      encapsulates logic within the model.

  - *Database Initialization and Migrations:* Explain how the module
    handles setting up the database tables. It likely
    calls Base.metadata.create_all(engine) at some point to create
    tables if they don’t exist. Also, if DatabaseMeta (which stores
    schema version) is present, describe how the application might use
    it: for example, on startup, check if
    the DatabaseMeta.version matches the expected DATABASE_VERSION; if
    not, run migration logic (possibly using importlib to run migration
    scripts, as hinted by the import of importlib and event). The manual
    should outline this procedure: how upgrades would be managed (e.g.,
    adding new columns or tables when the app version increases). If
    backup retention is involved, describe the possibility that the code
    might copy the current database to a backup file (maybe timestamped)
    and keep only the last 30 days of backups to avoid clutter.

  - *Launching the Application:* Finally, detail
    how poker_init.py likely ties everything together. It may contain
    logic such as: check Python version, set up logging, determine the
    path for the database file (perhaps in the user’s home directory or
    local folder), create the engine, define session_context,
    call seed_database to add default data, and then
    call poker_main.run(engine, session_context). If there is an if
    \_\_name\_\_ == "\_\_main\_\_": block, it would execute these steps.
    The manual should provide a clear sequence of these operations so a
    developer can understand the startup flow or replicate it if needed.

  - *Error Handling:* Note any try/except or logging of errors in this
    process. For instance, if the database file is locked or a migration
    fails, the code might log an error (since logging and traceback are
    imported). Emphasize the importance of these messages for debugging
    installation or runtime issues.

  - *Developer Tips:* Advise on how a developer can modify
    configurations here. For example, changing DEFAULT_CHIP_STACK will
    affect new players’ starting money, or
    adjusting BACKUP_RETENTION_DAYS will keep more/less backup files.
    This encourages understanding of how configuration is managed in
    code.
    *(If the repository includes additional modules or scripts not
    covered above, include similar breakdowns for each. For example, if
    there were a CLI interface or tests, outline their purpose. If not,
    the above three modules are the core.)*

## Installation and Configuration Guide

In the final section of the manual, provide a step-by-step guide for
    users (or developers) to install and run PokerTool, as well as how
    to configure it or troubleshoot common problems.

- **System Requirements:** List the prerequisites for running PokerTool.
  This includes having **Python 3.8 or higher** installed. Also note
  that Tkinter (the GUI library) is required – it comes packaged with
  standard Python on Windows/macOS, but on some Linux distributions the
  user may need to install it separately (e.g., via system package
  manager). Mention supported operating systems if relevant (PokerTool
  should run on any OS that supports Python and Tkinter). Ensure the
  user’s environment has network access disabled if needed (though
  PokerTool is local and doesn’t require internet).

- **Dependencies:** Provide instructions for installing required Python
  packages. If a requirements.txt or pyproject.toml is included in the
  repo, reference that. Otherwise, explicitly list needed libraries: at
  minimum **SQLAlchemy** (the version compatible with the code, e.g.,
  1.4 or 2.x as used), and possibly others (if the code uses additional
  packages like pytz or anything, but from what we see, primarily it’s
  SQLAlchemy and Tkinter). The manual should guide the user to run pip
  install sqlalchemy or pip install -r requirements.txt as appropriate.
  If the project is packaged, pip install pokertool (if applicable)
  could be mentioned.

- **Obtaining the PokerTool Code:** Explain where to get the PokerTool
  source or executable. For example: clone the GitHub repository
  (provide the URL) and check out the develop branch (if that’s the
  latest) or download a release archive. If the project offers an
  installer or compiled executable, mention that as an alternative. Make
  sure to specify the directory structure (so the user knows
  where poker_main.py and others reside).

- **Database Setup:** In most cases, the SQLite database will be created
  automatically on first run. The manual should clarify this: e.g.,
  “PokerTool uses an SQLite database file to store players and hand
  histories. By default, this file will be created in your user
  directory or the working directory the first time you run the app.” If
  the path is configurable or known (say pokertool.db or a file
  under ~/.pokertool/), mention the default location. Advise that no
  manual setup of the database is required; the application will set up
  the schema and seed the initial data (like the default player) on its
  own. However, also inform the user that if they delete this file or
  want to reset data, they can simply remove it and a new one will be
  generated.

- **Launching the Application:** Provide step-by-step on how to start
  PokerTool after installation:

  - If using source: “Open a terminal/command prompt in the PokerTool
    directory. Ensure your virtual environment (if used) is activated.
    Run python poker_init.py (or whichever is the main script) to start
    the application.” If the main entry is different, adjust
    accordingly. The manual should mention what the user will see –
    e.g., the Tkinter window should appear within a few seconds showing
    the Poker Assistant interface.

  - If using an executable or other distribution: detail how to run it
    (double-click, etc.).

  - Mention that on first run, there may be a short delay as the
    database is initialized, but subsequently it should open quickly. If
    any console output appears (like log messages or errors in the
    terminal), instruct the user to take note, as these can be useful
    for troubleshooting if something goes wrong.

- **Basic Configuration Options:** Explain any configurable settings the
  user or admin can change:

  - For example, if the database file path or name can be changed
    (perhaps by editing a constant or an environment variable), document
    that. There might not be a user-friendly way in the current state,
    but advanced users could modify poker_init.py constants (like to
    change DEFAULT_CHIP_STACK or initial bankroll). If the tool had a
    config file or CLI arguments, list them
    (e.g., --db-path, --reset-db etc., if they exist).

  - If the application uses logging, mention how to increase verbosity
    (maybe by editing a logging level in the code since logging is
    imported).

  - Any internationalization or UI configuration (unlikely at this
    stage, but mention font sizes or colors could only be changed by
    modifying the code). Essentially, note that PokerTool is currently a
    simple application without a lot of user-facing settings, but
    developers can tweak constants in the source if needed.

- **Troubleshooting and FAQs:** Provide help for common issues:

  - *GUI not launching:* If the program exits with no window, check that
    Tkinter is properly installed. On Linux, for instance, the user may
    need to install an OS package (python3-tk). If an error about
    Tkinter is shown, guide the user to install that and try again.

  - *Database locked or errors when recording history:* Instruct that
    this is uncommon for a single-user SQLite app, but if it happens,
    the user can close the application and ensure no other instance is
    running. If a corruption is suspected, the user can delete
    the pokertool database file and let it recreate (note: this will
    erase history). Emphasize using the in-app “Clear History” function
    to wipe records if needed rather than deleting the file, to avoid
    residual issues.

  - *Incorrect or surprising win probability:* Acknowledge that the
    calculation is simplified. The manual can reassure that this is not
    a bug but by design. However, if the values are extremely off (like
    always showing 5% or 95%), then it might indicate an issue (perhaps
    the ranges aren’t updating). Suggest restarting the app in such a
    case.

  - *Plugin errors:* If a plugin crashes (for example, an error occurs
    opening Hand History), the app will show a “Plugin Error” message.
    Advise the user to check the console for any traceback (developers
    can use that to debug). If it’s a known issue (like a missing
    dependency or an edge case), mention any known workaround or that it
    should be reported to the developers.

  - Include an FAQ entry if appropriate, e.g., **“Can I track multiple
    players or sessions?”** – Answer: The current UI is single-player
    (one profile “You”), but the underlying database is designed to
    handle multiple players and sessions. Future versions might expose
    this, or advanced users could manually add players to the database.

  - **“How do I update PokerTool?”** – Explain how to pull the latest
    version from the repository or if using pip, how to upgrade, being
    mindful that database schema changes might occur (though with
    versioning to handle it).

- **Contributing and Further Development:** (Optional) Encourage
  developers to contribute if the project is open-source. Point to where
  the code is modular to allow enhancements (for instance, improving the
  win probability algorithm or adding new plugins). Provide any
  guidelines for contributing, if available (code style, tests, etc.).
  If a test suite exists, mention how to run tests. This part can be
  brief, but it adds to the completeness of the manual for those
  interested in extending the tool.

## Conclusion and Next Steps

*(Wrap up the outline with a note on completing the manual.)* The
  above sections and points form the structure of the ultimate PokerTool
  user and developer manual (MANUAL.md). Each item will be expanded into
  detailed paragraphs, instructions, or code examples in the actual
  manual. Once this outline is reviewed and approved, the next step is
  to fill in each section with polished content, screenshots (if any GUI
  images are to be included), and possibly tables or diagrams for
  clarity. The goal is that by following this outline, we will produce a
  comprehensive guide that allows a new user to confidently use
  PokerTool and a new developer to understand and contribute to the
  PokerTool codebase.
