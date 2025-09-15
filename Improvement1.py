# PokerTool version 20
# Last updated: 2025-09-15
# Description: Updated Poker tool with improved architecture, bug fixes, and documentation.
# - Card: represents a playing card (rank & suit) with proper comparisons.
# - Deck: represents a standard 52-card deck with shuffle and deal functionality.
# - Player: represents a poker player (hole cards, best hand evaluation).
# - Hand evaluation: logic to rank 5-card poker hands (supports Texas Hold'em 7-card evaluation).
__version__ = "20"

import itertools
from collections import Counter

class Card:
    """Represents a standard playing card with rank and suit, and defines comparisons based on poker value."""
    # Valid ranks (2-9, Ten, Jack, Queen, King, Ace) and suits (Hearts, Diamonds, Clubs, Spades)
    RANKS = [str(n) for n in range(2, 10)] + ["T", "J", "Q", "K", "A"]
    SUITS = ["H", "D", "C", "S"]
    
    def __init__(self, rank: str, suit: str):
        # Normalize inputs to uppercase
        rank = rank.upper()
        suit = suit.upper()
        if rank not in Card.RANKS:
            raise ValueError(f"Invalid rank '{rank}'")
        if suit not in Card.SUITS:
            raise ValueError(f"Invalid suit '{suit}'")
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        """String representation of the card, e.g. 'AH' for Ace of Hearts."""
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        # Cards are equal if their ranks are equal (suits ignored for poker ranking):contentReference[oaicite:22]{index=22}
        return self.rank == other.rank
    
    def __lt__(self, other):
        if not isinstance(other, Card):
            return False
        # Compare cards by rank ordering (suits not considered):contentReference[oaicite:23]{index=23} 
        return Card.RANKS.index(self.rank) < Card.RANKS.index(other.rank)

class Deck:
    """Represents a deck of 52 playing cards. Can be shuffled and used to deal cards."""
    def __init__(self):
        # Initialize a standard 52-card deck (no jokers).
        self.cards = [Card(rank, suit) for suit in Card.SUITS for rank in Card.RANKS]
    
    def shuffle(self):
        """Shuffle the deck randomly using Python's random.shuffle."""
        import random
        random.shuffle(self.cards)
    
    def deal_card(self):
        """Deal one card from the deck. Removes and returns the top card of the deck."""
        if len(self.cards) == 0:
            raise IndexError("Cannot deal from an empty deck")
        return self.cards.pop()
    
    def deal_cards(self, count: int):
        """Deal a number of cards from the deck. Returns a list of Card objects."""
        if count < 0 or count > len(self.cards):
            raise ValueError("Cannot deal {} cards; deck has {}".format(count, len(self.cards)))
        dealt = self.cards[-count:]  # take from the bottom of list (top of deck)
        self.cards = self.cards[:-count]
        return dealt
    
    def __len__(self):
        """Return the number of cards remaining in the deck."""
        return len(self.cards)
    
    def __str__(self):
        """Return a space-separated string of all cards in the deck (mostly for debugging)."""
        return " ".join(str(card) for card in self.cards)

class Player:
    """Represents a poker player with hole cards and best hand evaluation."""
    def __init__(self, name: str):
        self.name = name
        self.hole_cards = []       # list of 2 Card objects
        self.best_hand = None      # list of 5 Card objects (best hand)
        self.best_hand_rank = None # tuple representing the best hand's rank for comparison
    
    def receive_card(self, card: Card):
        """Give the player a hole card. In Texas Hold'em, a player can have at most 2 hole cards."""
        if len(self.hole_cards) >= 2:
            raise ValueError("Player already has 2 hole cards")
        self.hole_cards.append(card)
    
    def reset_hand(self):
        """Reset the player's hand (clear hole_cards and best_hand). Call between rounds."""
        self.hole_cards.clear()
        self.best_hand = None
        self.best_hand_rank = None
    
    def update_best_hand(self, community_cards: list):
        """
        Determine the best 5-card poker hand from the player's hole cards and community cards.
        :param community_cards: list of Card (typically 5 community cards on the table).
        :return: the best 5-card hand (list of Card) and sets best_hand/best_hand_rank.
        """
        if len(self.hole_cards) != 2:
            raise ValueError("Player must have 2 hole cards to evaluate best hand")
        if len(community_cards) < 5:
            raise ValueError("Need 5 community cards to determine best hand")
        all_cards = self.hole_cards + community_cards
        best_rank = None
        best_combination = None
        # Check all 5-card combinations from the 7 cards:contentReference[oaicite:24]{index=24}
        for combo in itertools.combinations(all_cards, 5):
            rank = evaluate_hand(combo)
            if best_rank is None or rank > best_rank:
                best_rank = rank
                best_combination = combo
        # Save the best hand (sorted for readability) and its rank
        self.best_hand = sorted(list(best_combination), reverse=True)
        self.best_hand_rank = best_rank
        return self.best_hand
    
    def get_hole_cards_notation(self):
        """
        Return the hole cards in standard poker notation (e.g., 'AKs' for Ace-King suited, 'TT' for pair of Tens).
        - Two same ranks: just the rank twice (e.g., "KK").
        - Otherwise, add 's' if suited or 'o' if offsuit:contentReference[oaicite:25]{index=25}.
        """
        if len(self.hole_cards) != 2:
            return ""
        c1, c2 = sorted(self.hole_cards, reverse=True)  # sort by rank
        r1, r2 = c1.rank, c2.rank
        if r1 == r2:
            return r1 + r2  # pocket pair, e.g., "QQ"
        notation = r1 + r2
        notation += "s" if c1.suit == c2.suit else "o"
        return notation
    
    def __str__(self):
        return f"{self.name}: Hole {self.hole_cards}, Best {self.best_hand}"
    
    def __repr__(self):
        return str(self)

# Hand ranking categories for reference (0 = High Card, ... 9 = Royal Flush)
CATEGORY_NAMES = {
    0: "High Card",
    1: "Pair",
    2: "Two Pair",
    3: "Three of a Kind",
    4: "Straight",
    5: "Flush",
    6: "Full House",
    7: "Four of a Kind",
    8: "Straight Flush",
    9: "Royal Flush"
}

def evaluate_hand(cards):
    """
    Evaluate a 5-card poker hand and return a tuple (category, tiebreaker...) that can be used for comparison.
    The tuple's first element is the category rank (0=High Card, ..., 9=Royal Flush), and subsequent elements are values for tie-breaking.
    """
    # Ensure input is a 5-card iterable (tuple or list of Card)
    cards = list(cards)
    if len(cards) != 5:
        raise ValueError("Exactly 5 cards are required to evaluate a hand")
    # Convert ranks to numerical values for comparison
    rank_values = []
    for card in cards:
        r = card.rank
        if r.isdigit():
            rank_values.append(int(r))
        else:
            rank_values.append({"T":10, "J":11, "Q":12, "K":13, "A":14}[r])
    rank_values.sort(reverse=True)
    suits = [card.suit for card in cards]
    # Count occurrences of each rank
    counts = Counter(rank_values)
    # Sort ranks by count (desc) then by value (desc)
    # e.g., for hand [A,A,A,K,K] -> counts: {14:3, 13:2}, sorted_by_count -> [(14,3), (13,2)]
    sorted_counts = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    sorted_ranks = [rank for rank, cnt in sorted_counts]
    counts_list = [cnt for rank, cnt in sorted_counts]
    # Check for flush and straight
    flush = len(set(suits)) == 1
    unique_vals = sorted(set(rank_values))
    straight = False
    top_of_straight = None
    if len(unique_vals) == 5:
        # Normal straight: max-min == 4
        if max(unique_vals) - min(unique_vals) == 4:
            straight = True
            top_of_straight = max(unique_vals)
        # Ace-low straight (5-high straight: A,2,3,4,5):contentReference[oaicite:26]{index=26}
        if unique_vals == [2, 3, 4, 5, 14]:
            straight = True
            top_of_straight = 5  # treat 5 as the top value for the straight
            unique_vals = [1, 2, 3, 4, 5]  # adjust for tiebreaker purposes
    # Determine hand category
    category = None
    tiebreak = ()
    if counts_list == [4, 1]:
        # Four of a Kind
        category = 7
        four_val = sorted_ranks[0]
        kicker_val = sorted_ranks[1]
        tiebreak = (four_val, kicker_val)
    elif counts_list == [3, 2]:
        # Full House
        category = 6
        trip_val = sorted_ranks[0]
        pair_val = sorted_ranks[1]
        tiebreak = (trip_val, pair_val)
    elif flush and straight:
        # Straight Flush (or Royal Flush)
        if top_of_straight == 14 and min(unique_vals) == 10:
            category = 9  # Royal Flush:contentReference[oaicite:27]{index=27}
        else:
            category = 8  # Straight Flush
        # For straight/straight flush, tiebreaker is the top card value
        tiebreak = (top_of_straight,)
    elif flush:
        # Flush
        category = 5
        # Five cards sorted by value for tiebreaker
        tiebreak = tuple(sorted(rank_values, reverse=True))
    elif straight:
        # Straight
        category = 4
        tiebreak = (top_of_straight,)
    elif counts_list == [3, 1, 1]:
        # Three of a Kind
        category = 3
        trip_val = sorted_ranks[0]
        kickers = sorted(sorted_ranks[1:], reverse=True)
        tiebreak = tuple([trip_val] + kickers)
    elif counts_list == [2, 2, 1]:
        # Two Pair
        category = 2
        pair_high = sorted_ranks[0]
        pair_low = sorted_ranks[1]
        kicker_val = sorted_ranks[2]
        # Ensure pair_high is actually the higher value (sorted_ranks is already desc by count then value)
        if pair_high < pair_low:
            pair_high, pair_low = pair_low, pair_high
        tiebreak = (pair_high, pair_low, kicker_val)
    elif counts_list == [2, 1, 1, 1]:
        # One Pair
        category = 1
        pair_val = sorted_ranks[0]
        kickers = sorted(sorted_ranks[1:], reverse=True)
        tiebreak = tuple([pair_val] + kickers)
    else:
        # High Card
        category = 0
        tiebreak = tuple(sorted(rank_values, reverse=True))
    return (category,) + tiebreak

def compare_hands(hand1, hand2):
    """
    Compare two 5-card hands.
    :return: 1 if hand1 > hand2, -1 if hand1 < hand2, 0 if equal (tie).
    """
    score1 = evaluate_hand(hand1)
    score2 = evaluate_hand(hand2)
    if score1 > score2:
        return 1
    elif score1 < score2:
        return -1
    else:
        return 0

def determine_winners(players: list, community_cards: list):
    """
    Determine the winner(s) among players given the community cards.
    :return: list of Player objects who have the top hand (ties possible).
    """
    best_rank = None
    winners = []
    for player in players:
        player.update_best_hand(community_cards)
        if best_rank is None or player.best_hand_rank > best_rank:
            best_rank = player.best_hand_rank
            winners = [player]
        elif player.best_hand_rank == best_rank:
            winners.append(player)
    return winners

# Example usage (for manual testing, will run only if this file is executed directly)
if __name__ == "__main__":
    # Set up a quick demo round with 2 players
    deck = Deck()
    deck.shuffle()
    players = [Player("Alice"), Player("Bob")]
    # Deal 2 hole cards to each player
    for player in players:
        player.receive_card(deck.deal_card())
        player.receive_card(deck.deal_card())
    # Deal 5 community cards
    community = deck.deal_cards(5)
    # Determine each player's best hand
    for player in players:
        player.update_best_hand(community)
        print(f"{player.name} hole: {player.hole_cards} -> best hand: {player.best_hand} ({CATEGORY_NAMES[player.best_hand_rank[0]]})")
    # Determine winner(s)
    winners = determine_winners(players, community)
    if len(winners) == 1:
        print(f"Winner: {winners[0].name} with {CATEGORY_NAMES[winners[0].best_hand_rank[0]]}")
    else:
        print("It's a tie between: " + " and ".join(w.name for w in winners) + 
              f" with {CATEGORY_NAMES[winners[0].best_hand_rank[0]]}")
