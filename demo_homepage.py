"""Quick demo of the modern homepage UI.

Run this to see the homepage interface in action without running the full game.
"""

import pygame
import sys

# Add parent directory to path
sys.path.insert(0, '.')

from ui.modern_homepage import ModernHomePage

# Initialize pygame
pygame.init()

# Configuration
WINDOW_SIZE = {"width": 1920, "height": 1080}
FULLSCREEN = False  # Set to False to run windowed for testing

# Create display
if FULLSCREEN:
    screen = pygame.display.set_mode(
        (WINDOW_SIZE["width"], WINDOW_SIZE["height"]),
        pygame.FULLSCREEN
    )
else:
    screen = pygame.display.set_mode(
        (WINDOW_SIZE["width"], WINDOW_SIZE["height"])
    )

pygame.display.set_caption("Modern Gaming Homepage - Demo")

# Create homepage
homepage = ModernHomePage(WINDOW_SIZE, player_name="Player", coins=5000)

# Set button callbacks
def on_start():
    print("Start Game pressed!")

def on_shop():
    print("Shop pressed!")

def on_settings():
    print("Settings pressed!")

homepage.set_callbacks({
    "start": on_start,
    "shop": on_shop,
    "settings": on_settings,
})

# Main loop
clock = pygame.time.Clock()
running = True
frame_count = 0

print("Modern Homepage Demo started!")
print("- Click buttons to test interactions")
print("- Press ESC to exit")
print("- Press ENTER to 'start game'")
print(f"FPS: 120")

while running:
    delta_time = clock.tick(120) / 1000.0
    frame_count += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        action = homepage.handle_event(event)
        if action == "quit":
            running = False
            print("Quit requested")
            break
        if action == "start":
            print("Start Game action triggered!")

    # Update and draw
    homepage.update(delta_time)
    homepage.draw(screen)
    pygame.display.flip()

    # Print performance info every 120 frames (1 second)
    if frame_count % 120 == 0:
        print(f"Frame {frame_count} | FPS: {clock.get_fps():.1f}")

pygame.quit()
print("Demo ended")
