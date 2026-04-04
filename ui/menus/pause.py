"""Pause menu component.

Provides a modal pause menu with options to resume, restart, access
settings, or quit the game. Supports both keyboard and mouse navigation.
"""

from __future__ import annotations

from typing import List, Optional

import pygame

from ui.components.button import Button
from ui.core.constants import ANIMATION, COLORS, FONTS, LAYOUT
from ui.core.types import Event, MousePos, MousePressed, Surface
from ui.utils.drawing import draw_rounded_rect


class PauseMenu:
    """Pause menu with animated overlay and navigation.
    
    Displays a centered modal menu with resume, restart, settings, and
    quit options. Supports keyboard navigation (arrow keys, enter, escape)
    and mouse interaction. Features a fade-in animation when shown.
    
    Attributes:
        options: List of menu option labels.
        buttons: List of Button instances (recreated on layout updates).
        visible: True if the menu is currently displayed.
        anim_progress: Current fade-in animation progress (0.0-1.0).
        selected_index: Currently selected option index for keyboard nav.
        font_title: Font for the "PAUSED" title.
        font_option: Font for button labels.
        font_hint: Font for keyboard hint text.
        accent_color: Primary accent color.
        text_color: Default text color.
        muted_color: Secondary/muted text color.
    """

    def __init__(self) -> None:
        """Initialize the pause menu.
        
        Sets up fonts, colors, and initial state. Buttons are created
        dynamically when the menu is drawn via update_layout.
        """
        self.font_title: pygame.font.Font = pygame.font.Font(None, FONTS.title)
        self.font_option: pygame.font.Font = pygame.font.Font(None, FONTS.option)
        self.font_hint: pygame.font.Font = pygame.font.Font(None, FONTS.hint)

        self.accent_color: pygame.Color = pygame.Color(COLORS.accent)
        self.text_color: pygame.Color = pygame.Color(COLORS.text)
        self.muted_color: pygame.Color = pygame.Color(COLORS.muted)

        self.options: List[str] = ["Resume", "Restart", "Settings", "Quit"]
        self.buttons: List[Button] = []
        self._clicked_option: Optional[str] = None

        self.visible: bool = False
        self.anim_progress: float = 0.0

    def show(self) -> None:
        """Show the pause menu and reset animation.
        
        Sets the menu to visible and resets the fade-in animation
        progress to 0.0 for a smooth entry animation.
        
        Returns:
            None
        """
        self.visible = True
        self.anim_progress = 0.0

    def hide(self) -> None:
        """Hide the pause menu.
        
        Sets the menu to invisible. Animation progress is preserved
        but will be reset on next show().
        
        Returns:
            None
        """
        self.visible = False

    def update_layout(self, screen_width: int, screen_height: int) -> None:
        """Recalculate button positions based on screen dimensions.
        
        Creates Button instances positioned within the centered menu panel.
        Called automatically during draw() to ensure responsive layout.
        
        Args:
            screen_width: Current screen width in pixels.
            screen_height: Current screen height in pixels.
            
        Returns:
            None
        """
        menu_w: int = LAYOUT.pause_menu_width
        menu_h: int = LAYOUT.pause_menu_height
        menu_x: int = screen_width // 2 - menu_w // 2
        menu_y: int = screen_height // 2 - menu_h // 2

        self.buttons = []
        for i, option in enumerate(self.options):
            btn: Button = Button(
                menu_x + 40,
                menu_y + 120 + i * ANIMATION.menu_button_spacing,
                menu_w - 80,
                48,
                option,
            )
            self.buttons.append(btn)

    def handle_input(self, event: Event) -> Optional[str]:
        """Process input events for menu navigation.
        
        Handles keyboard navigation (UP/DOWN arrows, ENTER, ESCAPE) and
        mouse clicks on buttons. Returns the selected option string when
        an action is triggered.
        
        Args:
            event: A pygame event object.
            
        Returns:
            The selected option name ("Resume", "Restart", "Settings", "Quit")
            if an action was triggered, or None if no action occurred.
        """
        if not self.visible:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "Resume"
            elif event.key == pygame.K_UP:
                self.selected_index = (getattr(self, "selected_index", 0) - 1) % len(
                    self.options
                )
                setattr(
                    self,
                    "selected_index",
                    (getattr(self, "selected_index", 0) - 1) % len(self.options),
                )
            elif event.key == pygame.K_DOWN:
                setattr(
                    self,
                    "selected_index",
                    (getattr(self, "selected_index", 0) + 1) % len(self.options),
                )
            elif event.key == pygame.K_RETURN:
                idx: int = getattr(self, "selected_index", 0)
                return self.options[idx]

        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    return btn.text

        return None

    def update(self, mouse_pos: MousePos, mouse_pressed: MousePressed) -> None:
        """Update button hover states and detect clicks.
        
        Updates all buttons with current mouse state to handle hover
        effects. Click detection is primarily handled by handle_input
        for immediate response, but this method tracks state changes.
        
        Args:
            mouse_pos: Current (x, y) position of the mouse cursor.
            mouse_pressed: Tuple of mouse button states.
            
        Returns:
            None
        """
        if not self.visible:
            return

        clicked: Optional[str] = None
        for btn in self.buttons:
            was_hovered: bool = btn.is_hovered
            btn.update(mouse_pos, mouse_pressed)
            if mouse_pressed[0] and btn.is_hovered and not was_hovered:
                clicked = btn.text

        if clicked:
            self._clicked_option = clicked

    def draw(self, screen: Surface, dt: float = 0.016) -> None:
        """Render the pause menu to the given screen.
        
        Draws the animated overlay, centered menu panel with title,
        option buttons, and keyboard hints. Updates animation progress
        each frame for smooth fade-in effect.
        
        Args:
            screen: The pygame surface to draw on.
            dt: Delta time since last frame for animation timing.
            
        Returns:
            None
        """
        if not self.visible:
            return

        self.anim_progress = min(1.0, self.anim_progress + dt * ANIMATION.pause_fade_speed)

        sw: int = screen.get_width()
        sh: int = screen.get_height()

        overlay: Surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * self.anim_progress)))
        screen.blit(overlay, (0, 0))

        menu_w: int = LAYOUT.pause_menu_width
        menu_h: int = LAYOUT.pause_menu_height
        menu_x: int = sw // 2 - menu_w // 2
        menu_y: int = sh // 2 - menu_h // 2

        draw_rounded_rect(screen, (20, 30, 50, 240), (menu_x, menu_y, menu_w, menu_h))
        draw_rounded_rect(screen, self.accent_color, (menu_x, menu_y, menu_w, 4))
        draw_rounded_rect(
            screen, self.accent_color, (menu_x, menu_y, menu_w, menu_h), 1
        )

        title: Surface = self.font_title.render("PAUSED", True, self.accent_color)
        screen.blit(title, (sw // 2 - title.get_width() // 2, menu_y + 25))

        self.update_layout(sw, sh)

        for btn in self.buttons:
            btn.draw(screen)

        hint: Surface = self.font_hint.render(
            "↑↓ Navigate  |  ENTER Select  |  ESC Resume", True, self.muted_color
        )
        screen.blit(hint, (sw // 2 - hint.get_width() // 2, menu_y + menu_h - 30))
