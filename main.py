import logging
import os

import pygame

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
    """Initialize the game and run the main loop."""
    pygame.init()

    settings = Settings()

    flags = pygame.FULLSCREEN if settings.fullscreen else pygame.RESIZABLE
    resolution = (int(settings.resolution[0]), int(settings.resolution[1]))
    try:
        screen = pygame.display.set_mode(resolution, flags, vsync=1 if settings.vsync else 0)
    except TypeError:
        screen = pygame.display.set_mode(resolution, flags)

    pygame.display.set_caption("Hand Gesture Racing Game")
    clock = pygame.time.Clock()

    runtime_window_size = {
        "width": screen.get_width(),
        "height": screen.get_height(),
    }

    car_manager = CarManager()

    # Create shop screen (car selection interface)
    shop_screen = HomePageScreen(runtime_window_size, car_manager)

    # Use modern homepage for main menu
    homepage = ModernHomePage(runtime_window_size, player_name="Player", coins=car_manager.credits)

    # Create settings menu
    settings_menu = SettingsMenu()

    game_map = Map(runtime_window_size, lane_count=settings.lane_count)

    start_x = runtime_window_size["width"] // 2
    start_y = runtime_window_size["height"] - 240
    player_car = PlayerCar(start_x, start_y, car_manager=car_manager)

    detector = Controller()

    hud_font = pygame.font.Font(None, 32)
    hud = PlayerHUD(player_car, detector, hud_font)

    game_hud = HUDManager(
        runtime_window_size["width"],
        runtime_window_size["height"],
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
        window_size=runtime_window_size,
        homepage=homepage,
        shop_screen=shop_screen,
        car_manager=car_manager,
    )

    game_loop.initialize()

    try:
        game_loop.run()
    except Exception as exc:
        logger.exception("Game loop crashed: %s", exc)
        raise


if __name__ == "__main__":
    main()
