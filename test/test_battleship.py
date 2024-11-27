from typing import List, Optional
from enum import Enum
import random
from server.py.game import Game, Player

class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'

class GamePhase(str, Enum):
    SETUP = 'setup'
    RUNNING = 'running'
    FINISHED = 'finished'

class BattleshipAction:
    def __init__(self, action_type: ActionType, ship_name: Optional[str], location: List[str]) -> None:
        self.action_type: ActionType = action_type
        self.ship_name: Optional[str] = ship_name
        self.location: List[str] = location

class Ship:
    def __init__(self, name: str, length: int, location: Optional[List[str]] = None) -> None:
        self.name: str = name
        self.length: int = length
        self.location: Optional[List[str]] = location

class PlayerState:
    def __init__(self, name: str, ships: List[Ship], shots: List[str], successful_shots: List[str]) -> None:
        self.name: str = name
        self.ships: List[Ship] = ships
        self.shots: List[str] = shots
        self.successful_shots: List[str] = successful_shots

class BattleshipGameState:
    def __init__(self, idx_player_active: int, phase: GamePhase, winner: Optional[int], players: List[PlayerState]) -> None:
        self.idx_player_active: int = idx_player_active
        self.phase: GamePhase = phase
        self.winner: Optional[int] = winner
        self.players: List[PlayerState] = players

class Battleship(Game):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        ship_templates = [
            Ship("carrier", 5),
            Ship("battleship", 4),
            Ship("cruiser", 3),
            Ship("submarine", 3),
            Ship("destroyer", 2)
        ]
        players = [
            PlayerState("Player 1", [Ship(ship.name, ship.length) for ship in ship_templates], [], []),
            PlayerState("Player 2", [Ship(ship.name, ship.length) for ship in ship_templates], [], [])
        ]
        self.state = BattleshipGameState(0, GamePhase.SETUP, None, players)

    def print_state(self) -> None:
        print(f"Active player: {self.state.players[self.state.idx_player_active].name}")
        print(f"Phase: {self.state.phase}")
        print(f"Winner: {self.state.winner}")
        for player in self.state.players:
            print(f"{player.name}:")
            print(f"  Ships: {[f'{ship.name}: {ship.location}' for ship in player.ships]}")
            print(f"  Shots: {player.shots}")
            print(f"  Successful shots: {player.successful_shots}")

    def get_state(self) -> BattleshipGameState:
        return self.state

    def set_state(self, state: BattleshipGameState) -> None:
        self.state = state

    def get_list_action(self) -> List[BattleshipAction]:
        actions: List[BattleshipAction] = []
        if self.state.phase == GamePhase.SETUP:
            player = self.state.players[self.state.idx_player_active]
            occupied_cells = set(cell for ship in player.ships if ship.location for cell in ship.location)
            for ship in player.ships:
                if ship.location is None:
                    for x in range(10):
                        for y in range(10):
                            # Horizontal placement
                            if x + ship.length <= 10:
                                location = [f"{chr(65+x+i)}{y+1}" for i in range(ship.length)]
                                if not set(location) & occupied_cells:
                                    actions.append(BattleshipAction(ActionType.SET_SHIP, ship.name, location))
                            # Vertical placement
                            if y + ship.length <= 10:
                                location = [f"{chr(65+x)}{y+1+i}" for i in range(ship.length)]
                                if not set(location) & occupied_cells:
                                    actions.append(BattleshipAction(ActionType.SET_SHIP, ship.name, location))
        elif self.state.phase == GamePhase.RUNNING:
            player = self.state.players[self.state.idx_player_active]
            occupied_locations = set(player.shots)
            for x in range(10):
                for y in range(10):
                    location = f"{chr(65+x)}{y+1}"
                    if location not in occupied_locations:
                        actions.append(BattleshipAction(ActionType.SHOOT, None, [location]))
        return actions

    def apply_action(self, action: BattleshipAction) -> None:
        player = self.state.players[self.state.idx_player_active]
        if action.action_type == ActionType.SET_SHIP:
            # Place the ship if it hasn't been placed yet
            for ship in player.ships:
                if ship.name == action.ship_name and ship.location is None:
                    ship.location = action.location
                    break
            # Switch to the next player
            self.state.idx_player_active = 1 - self.state.idx_player_active
            # Check if all ships for both players have been placed
            all_ships_placed = all(
                all(ship.location is not None for ship in p.ships)
                for p in self.state.players
            )
            if all_ships_placed:
                self.state.phase = GamePhase.RUNNING
                self.state.idx_player_active = 0  # Player 1 starts
        elif action.action_type == ActionType.SHOOT:
            if self.state.phase != GamePhase.RUNNING:
                return  # Cannot shoot before game has started
            opponent = self.state.players[1 - self.state.idx_player_active]
            if action.location[0] in player.shots:
                return  # Already shot at this location
            player.shots.append(action.location[0])
            if any(action.location[0] in ship.location for ship in opponent.ships if ship.location):
                player.successful_shots.append(action.location[0])
                if all(
                    all(loc in player.successful_shots for loc in ship.location)
                    for ship in opponent.ships if ship.location
                ):
                    self.state.winner = self.state.idx_player_active
                    self.state.phase = GamePhase.FINISHED
            # Switch to the next player if the game is not finished
            if self.state.phase != GamePhase.FINISHED:
                self.state.idx_player_active = 1 - self.state.idx_player_active

    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        masked_players = []
        for i, player in enumerate(self.state.players):
            if i == idx_player:
                masked_players.append(player)
            else:
                masked_ships = [Ship(ship.name, ship.length) for ship in player.ships]
                masked_player = PlayerState(
                    name=player.name,
                    ships=masked_ships,
                    shots=player.shots,
                    successful_shots=player.successful_shots
                )
                masked_players.append(masked_player)
        return BattleshipGameState(
            idx_player_active=self.state.idx_player_active,
            phase=self.state.phase,
            winner=self.state.winner,
            players=masked_players
        )

class RandomPlayer(Player):
    def select_action(self, state: BattleshipGameState, actions: List[BattleshipAction]) -> Optional[BattleshipAction]:
        if actions:
            return random.choice(actions)
        return None

if __name__ == "__main__":
    game = Battleship()
    player1 = RandomPlayer()
    player2 = RandomPlayer()
    players = [player1, player2]
    while game.get_state().phase != GamePhase.FINISHED:
        state = game.get_player_view(game.state.idx_player_active)
        actions = game.get_list_action()
        action = players[game.state.idx_player_active].select_action(state, actions)
        if action:
            game.apply_action(action)
    print("Final game state:")
    game.print_state()
