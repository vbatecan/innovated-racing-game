import logging
import os

import pygame

import config
from config import WINDOW_SIZE
from controller import Controller
from core.game_loop import GameLoop
from environment.map import Map
from models.car_manager import CarManager
from models.player_car import PlayerCar
from settings import Settings
from ui.game_ui import HUDManager, PauseMenu, SettingsMenu
from ui.homepage import HomePageScreen
from ui.modern_homepage import ModernHomePage
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
    screen = pygame.display.set_mode(
        (WINDOW_SIZE["width"], WINDOW_SIZE["height"]), pygame.FULLSCREEN
    )
    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()

    car_manager = CarManager()

    # Create shop screen (car selection interface)
    shop_screen = HomePageScreen(WINDOW_SIZE, car_manager)

    # Use modern homepage for main menu
    homepage = ModernHomePage(WINDOW_SIZE, player_name="Player", coins=1000)

    # Create settings menu
    settings_menu = SettingsMenu()

    settings = Settings()
    settings.fullscreen = True
    settings.show_camera = config.SHOW_CAMERA
    game_map = Map(WINDOW_SIZE, lane_count=settings.lane_count)

    start_x = WINDOW_SIZE["width"] // 2
    start_y = WINDOW_SIZE["height"] - 240
    player_car = PlayerCar(start_x, start_y, car_manager=car_manager)

    detector = Controller()
    # Note: detector.start_stream() is now called in GameLoop.run() after menu

    # Create font for HUD
    hud_font = pygame.font.Font(None, 32)
    hud = PlayerHUD(player_car, detector, hud_font)
    
    game_hud = HUDManager(
        WINDOW_SIZE["width"],
        WINDOW_SIZE["height"]
    )
    
    pause_menu = PauseMenu()

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
        homepage=homepage,
        shop_screen=shop_screen,
    )

    game_loop.initialize()

    try:
        game_loop.run()
    except Exception as e:
        logger.exception("Game loop crashed: %s", e)
        raise


if __name__ == "__main__":
    main()
