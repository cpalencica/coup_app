"""
Interactive loop to play Coup actions between players.

Run from the `backend` directory:
    python scripts\play_as_player.py

Features:
- Play as whichever player is the current turn — when turns rotate you can
  enter actions for each player.
- Add coins to players to test coup/assassinate conditions.
- Block actions (other players can declare a block and be challenged).
- Challenge actor claims (other players can challenge declared actions).
- The loop continues until one player remains or you quit.
"""
import os
import sys

# Make sure `app` package is importable when running from backend
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.game.engine import GameEngine
from app.game.actions import Action
from app.game.cards import Card


ACTION_MAP = {a.value: a for a in Action}
CARD_MAP = {c.value.lower(): c for c in Card}


def print_state(eng):
    print("\n=== Game State ===")
    for p in eng.state.players:
        print(f"Player {p.id} ({p.name}): coins={p.coins}, cards={[c.value for c in p.cards]}, alive={p.is_alive()}")
    print(f"Current player idx: {eng.state.current_player_idx}\n")


def prompt_action():
    print("Available actions:")
    print(", ".join([a.value for a in Action if a not in (Action.BLOCK, Action.CHALLENGE)]))
    action_in = input("Enter action: ").strip()
    if action_in not in ACTION_MAP:
        print("Unknown action")
        return None
    return ACTION_MAP[action_in]


def main():
    eng = GameEngine()
    eng.add_player(1, "Alice")
    eng.add_player(2, "Bob")
    eng.start()

    # Main game loop
    while True:
        print_state(eng)
        current = eng.current_player()
        print(f"Current turn: Player {current.id} ({current.name})")

        # Check for winner
        alive = [p for p in eng.state.players if p.is_alive()]
        if len(alive) <= 1:
            if alive:
                print(f"Player {alive[0].id} ({alive[0].name}) wins!")
            else:
                print("No players remaining. Game over.")
            break

        cmd = input("Choose: (a)dd coins, (p)lay action, (s)tate, (q)uit: ").strip().lower()
        if cmd == 'q':
            print("Quitting game")
            break
        if cmd == 's':
            continue
        if cmd == 'a':
            pid_in = input("Enter player id to add coins to (blank=current): ").strip()
            if pid_in == '':
                pid = current.id
            else:
                try:
                    pid = int(pid_in)
                except Exception:
                    print("Invalid player id")
                    continue
            amt_in = input("Enter number of coins to add: ").strip()
            try:
                amt = int(amt_in)
            except Exception:
                print("Invalid amount")
                continue
            target_player = eng.state.get_player(pid)
            if target_player is None:
                print("No such player")
                continue
            target_player.add_coins(amt)
            print(f"Added {amt} coins to player {pid}")
            continue

        if cmd == 'p':
            action = prompt_action()
            if action is None:
                continue

            target_id = None
            if action in (Action.COUP, Action.ASSASSINATE, Action.STEAL):
                tid = input("Enter target player id: ").strip()
                try:
                    target_id = int(tid)
                except Exception:
                    print("Invalid target id")
                    continue

            try:
                msg = eng.declare_action(current.id, action, target_id)
                print("declare_action:", msg)
            except Exception as e:
                print("declare_action failed:", e)
                continue

            # BLOCK PHASE
            if eng.state.awaiting_block:
                blocked = False
                for p in eng.state.players:
                    if not p.is_alive() or p.id == current.id:
                        continue
                    ans = input(f"Player {p.id} ({p.name}) block this action? (y/N): ").strip().lower()
                    if ans == 'y':
                        # prompt for block card
                        print("Block card options:", ", ".join([c.value for c in Card]))
                        card_in = input("Enter block card name (e.g. Contessa): ").strip().lower()
                        card = CARD_MAP.get(card_in)
                        if card is None:
                            print("Unknown card; cancelling block")
                            continue
                        eng.block(p.id, card)
                        print(f"Player {p.id} declared a block with {card.value}")
                        blocked = True
                        break

                # If a block was declared, allow challenges to the block
                if blocked and eng.state.awaiting_challenge:
                    for p in eng.state.players:
                        if not p.is_alive():
                            continue
                        if p.id == eng.state.pending_blocker:
                            continue
                        ans = input(f"Player {p.id} ({p.name}) challenge the block? (y/N): ").strip().lower()
                        if ans == 'y':
                            msg = eng.challenge(p.id)
                            print("challenge:", msg)
                            break

                    # if challenge canceled action
                    if eng.state.pending_action is None:
                        print("Action was cancelled due to successful challenge")
                        continue

            # CHALLENGE PHASE (when no block or after block resolved and still awaiting_challenge)
            if eng.state.awaiting_challenge:
                for p in eng.state.players:
                    if not p.is_alive() or p.id == current.id:
                        continue
                    ans = input(f"Player {p.id} ({p.name}) challenge the actor's claim? (y/N): ").strip().lower()
                    if ans == 'y':
                        msg = eng.challenge(p.id)
                        print("challenge:", msg)
                        break

                if eng.state.pending_action is None:
                    print("Action was cancelled due to successful challenge")
                    continue

            # RESOLVE
            res = eng.resolve()
            print("resolve:", res)
            continue

        print("Unknown command")


if __name__ == '__main__':
    main()
