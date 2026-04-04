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

    # State tracking for menu navigation
    current_screen = "home"  # Can be 'home', 'shop', 'settings', or 'game'

    def start_game() -> None:
        """Callback for start game button."""
        nonlocal current_screen
        current_screen = "game"

    def go_to_shop() -> None:
        """Callback for shop button - show car shop."""
        nonlocal current_screen
        current_screen = "shop"

    def go_to_settings() -> None:
        """Callback for settings button - show settings menu."""
        nonlocal current_screen
        current_screen = "settings"

    def return_to_menu() -> None:
        """Callback for returning from shop to menu."""
        nonlocal current_screen
        current_screen = "home"

    homepage.set_callbacks({
        "start": start_game,
        "shop": go_to_shop,
        "settings": go_to_settings,
    })

    # Main menu/shop navigation loop
    menu_running = True
    while menu_running:
        delta_time = clock.tick(120) / 1000.0

        if current_screen == "home":
            # Main menu screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                action = homepage.handle_event(event)
                if action == "quit":
                    pygame.quit()
                    return

            homepage.update(delta_time)
            homepage.draw(screen)
            pygame.display.flip()

            if current_screen == "game":
                menu_running = False

        elif current_screen == "shop":
            # Shop (car selection) screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                action = shop_screen.handle_event(event)
                if action == "quit":  # ESC key in shop returns to menu
                    current_screen = "home"
                elif action == "start":  # Car selected, proceed to game
                    current_screen = "game"
                    menu_running = False

            shop_screen.update(delta_time)
            shop_screen.draw(screen)
            pygame.display.flip()

        elif current_screen == "settings":
            # Settings menu screen
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                result = settings_menu.handle_input(event, mouse_pos)
                if result and result.get("action") == "close":
                    current_screen = "home"

            # Draw background
            screen.fill((10, 12, 24))
            
            # Update and draw settings menu
            settings_menu.update(mouse_pos)
            settings_menu.draw(screen)
            pygame.display.flip()

    settings = Settings()
    settings.fullscreen = True
    settings.show_camera = config.SHOW_CAMERA
    game_map = Map(WINDOW_SIZE, lane_count=settings.lane_count)

    start_x = WINDOW_SIZE["width"] // 2
    start_y = WINDOW_SIZE["height"] - 240
    player_car = PlayerCar(start_x, start_y, car_manager=car_manager)

    detector = Controller()
    detector.start_stream()

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
    )

    game_loop.initialize()

    try:
        game_loop.run()
    except Exception as e:
        logger.exception("Game loop crashed: %s", e)
        raise


if __name__ == "__main__":
    main()
