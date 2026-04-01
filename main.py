"""Main entry point for the Hand Gesture Racing Game.

Initializes Pygame, sets up all game components, and delegates to the
GameLoop class for the main game execution.
"""

import logging
import os

import pygame

import config
from config import WINDOW_SIZE
from controller import Controller
from core.game_loop import GameLoop
from environment.map import Map
from models.player_car import PlayerCar
from settings import Settings
from ui.game_ui import HUDManager, PauseMenu, SettingsMenu
from ui.hud import PlayerHUD

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initialize the game and run the main loop.

    Sets up Pygame, the player car, map, controller, and settings menu, then
    delegates to GameLoop for frame processing until exit.
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE["width"], WINDOW_SIZE["height"]))
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, config.FONT_SIZE)

    settings = Settings()
    settings.show_camera = config.SHOW_CAMERA
    game_map = Map(WINDOW_SIZE, lane_count=settings.lane_count)

    start_x = WINDOW_SIZE["width"] // 2
    start_y = WINDOW_SIZE["height"] - 240
    player_car = PlayerCar(start_x, start_y)

    detector = Controller()
    detector.start_stream()

    hud = PlayerHUD(player_car, detector, font)
    game_hud = HUDManager(
        screen_width=WINDOW_SIZE["width"],
        screen_height=WINDOW_SIZE["height"]
    )
    pause_menu = PauseMenu()
    settings_menu = SettingsMenu()

    game_loop = GameLoop(
        screen=screen,
        clock=clock,
        player_car=player_car,
        game_map=game_map,
        detector=detector,
        settings=settings,
        hud=hud,
        game_hud=game_hud,
        pause_menu=pause_menu,
        settings_menu=settings_menu,
        window_size=WINDOW_SIZE,
    )

    game_loop.initialize()

    try:
        game_loop.run()
    except Exception as e:
        logger.exception("Game loop crashed: %s", e)
        raise


if __name__ == "__main__":
    main()
