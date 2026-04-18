"""Shop and car-selection screen for the racing game.

Redesigned as a fast, grid/card-based storefront with category tabs, featured
badges, premium item emphasis, compact stat displays, and controller-friendly
navigation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygame

from models.car_data import CARS, Car
from models.car_manager import CarManager
from models.upgrades import UPGRADES


@dataclass
class ShopItem:
    """Single catalog item rendered as a card in the shop grid."""

    id: str
    category: str
    name: str
    price: int
    badge: str
    premium: bool
    key_stats: dict[str, int | str]
    unlock_score: int = 0
    car_id: Optional[int] = None
    image_path: str = ""
    comparison: list[tuple[str, int, int]] | None = None


class HomePageScreen:
    """Polished, fast shop experience with keyboard/mouse/controller support."""

    GRID_COLS = 4

    def __init__(self, window_size: dict[str, int], car_manager: CarManager) -> None:
        self.width = window_size["width"]
        self.height = window_size["height"]
        self.car_manager = car_manager

        self.title_font = pygame.font.Font(None, 66)
        self.section_font = pygame.font.Font(None, 38)
        self.body_font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 20)

        # High-contrast palette optimized for readability.
        self.bg_top = (8, 13, 24)
        self.bg_bottom = (26, 38, 58)
        self.panel = (18, 26, 40)
        self.card = (26, 36, 54)
        self.card_locked = (22, 26, 34)
        self.text = (242, 246, 255)
        self.muted = (164, 180, 205)
        self.accent = (84, 214, 255)
        self.accent_warm = (255, 193, 87)
        self.good = (90, 238, 162)
        self.danger = (255, 140, 140)

        self.categories = ["Cars", "Upgrades", "Skins", "Boosts"]
        self._active_category = 0

        self._elapsed = 0.0
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._mouse_pressed: tuple[bool, bool, bool] = (False, False, False)

        # Focus zones for keyboard/controller traversal.
        self._focus_zone = "cards"  # tabs | cards | actions | dialog
        self._selected_card_index = 0
        self._selected_action = 0  # 0=start, 1=back
        self._dialog_action = 0  # 0=buy, 1=cancel

        self._tab_rects: list[pygame.Rect] = []
        self.card_rects: list[pygame.Rect] = []
        self._action_rects: list[pygame.Rect] = []

        self._message_text: str | None = None
        self._message_timer = 0.0

        self._dialog_visible = False
        self._dialog_item: ShopItem | None = None

        self._car_images: dict[int, pygame.Surface] = {}
        self._catalog: list[ShopItem] = self._build_catalog()
        self._items: list[ShopItem] = []

        # Upgrades and credits are persisted by CarManager.

        self._load_car_images()
        self._sync_selected_to_manager()
        self._refresh_items()

    @property
    def selected_car(self) -> Car:
        """Get currently selected car object from the manager or fallback."""
        selected = self.car_manager.get_selected_car()
        return selected if selected else CARS[0]

    def _build_catalog(self) -> list[ShopItem]:
        items: list[ShopItem] = []

        for car in CARS:
            badge = "New"
            if car.rarity in ("Epic", "Legendary"):
                badge = "Hot"
            if car.id == CARS[-1].id:
                badge = "Limited"

            price = 0 if car.unlock_score == 0 else 600 + car.unlock_score // 20
            items.append(
                ShopItem(
                    id=f"car-{car.id}",
                    category="Cars",
                    name=car.name,
                    price=price,
                    badge=badge,
                    premium=car.rarity in ("Epic", "Legendary"),
                    key_stats={
                        "speed": int(car.stats.speed),
                        "handling": int(car.stats.handling),
                        "acceleration": int(car.stats.acceleration),
                    },
                    unlock_score=int(car.unlock_score),
                    car_id=car.id,
                    image_path=car.image_path,
                )
            )

        items.extend(
            [
                ShopItem(
                    id="turbo_charger",
                    category="Upgrades",
                    name="Turbo Charger",
                    price=980,
                    badge="Hot",
                    premium=True,
                    key_stats={"speed": "+12", "acceleration": "+10"},
                    comparison=[("SPD", 82, 94), ("ACC", 70, 80)],
                ),
                ShopItem(
                    id="sport_suspension",
                    category="Upgrades",
                    name="Sport Suspension",
                    price=740,
                    badge="New",
                    premium=False,
                    key_stats={"handling": "+14", "stability": "+8"},
                    comparison=[("HND", 68, 82), ("STB", 60, 68)],
                ),
                ShopItem(
                    id="precision_brakes",
                    category="Upgrades",
                    name="Precision Brakes",
                    price=620,
                    badge="Limited",
                    premium=False,
                    key_stats={"handling": "+10", "response": "+9"},
                    comparison=[("HND", 70, 80), ("RSP", 64, 73)],
                ),
            ]
        )

        items.extend(
            [
                ShopItem(
                    id="skin-carbon",
                    category="Skins",
                    name="Carbon Apex",
                    price=520,
                    badge="New",
                    premium=False,
                    key_stats={"finish": "Matte", "rarity": "Rare"},
                ),
                ShopItem(
                    id="skin-neon",
                    category="Skins",
                    name="Neon Pulse",
                    price=880,
                    badge="Hot",
                    premium=True,
                    key_stats={"finish": "Glow", "rarity": "Epic"},
                ),
                ShopItem(
                    id="skin-retro",
                    category="Skins",
                    name="Retro Stripe",
                    price=420,
                    badge="Limited",
                    premium=False,
                    key_stats={"finish": "Classic", "rarity": "Common"},
                ),
            ]
        )

        items.extend(
            [
                ShopItem(
                    id="boost-baseline",
                    category="Boosts",
                    name="Starter Nitro",
                    price=0,
                    badge="New",
                    premium=False,
                    key_stats={"duration": "2.0s", "power": "+15%"},
                ),
                ShopItem(
                    id="boost-overdrive",
                    category="Boosts",
                    name="Overdrive Pack",
                    price=660,
                    badge="Hot",
                    premium=True,
                    key_stats={"duration": "3.5s", "power": "+24%"},
                ),
                ShopItem(
                    id="boost-quantum",
                    category="Boosts",
                    name="Quantum Burst",
                    price=1050,
                    badge="Limited",
                    premium=True,
                    key_stats={"duration": "4.0s", "power": "+30%"},
                ),
            ]
        )

        return items

    def _load_car_images(self) -> None:
        for car in CARS:
            path = Path(car.image_path)
            if not path.exists():
                continue
            try:
                self._car_images[car.id] = pygame.image.load(str(path)).convert_alpha()
            except pygame.error:
                continue

    def _sync_selected_to_manager(self) -> None:
        selected = self.car_manager.get_selected_car()
        if not selected:
            return
        # Keep card cursor aligned with selected car when entering Cars tab.
        for idx, item in enumerate([i for i in self._catalog if i.category == "Cars"]):
            if item.car_id == selected.id:
                self._selected_card_index = idx
                break

    def _refresh_items(self) -> None:
        category = self.categories[self._active_category]
        self._items = [item for item in self._catalog if item.category == category]
        if not self._items:
            self._selected_card_index = 0
            return
        self._selected_card_index = max(0, min(self._selected_card_index, len(self._items) - 1))

        if category == "Cars":
            selected = self.car_manager.get_selected_car()
            if selected:
                for index, item in enumerate(self._items):
                    if item.car_id == selected.id:
                        self._selected_card_index = index
                        break

    def update(self, delta_time: float) -> None:
        self._elapsed += delta_time
        if self._message_timer > 0.0:
            self._message_timer = max(0.0, self._message_timer - delta_time)
            if self._message_timer == 0.0:
                self._message_text = None

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._dialog_visible:
                self._handle_dialog_click(event.pos)
                return None

            for index, rect in enumerate(self._tab_rects):
                if rect.collidepoint(event.pos):
                    self._active_category = index
                    self._focus_zone = "tabs"
                    self._refresh_items()
                    return None

            for index, rect in enumerate(self.card_rects):
                if rect.collidepoint(event.pos):
                    self._selected_card_index = index
                    self._focus_zone = "cards"
                    self._activate_selected_item()
                    return None

            for index, rect in enumerate(self._action_rects):
                if rect.collidepoint(event.pos):
                    self._selected_action = index
                    self._focus_zone = "actions"
                    if index == 0:
                        return self.start_game()
                    return "quit"

        if event.type == pygame.KEYDOWN:
            if self._dialog_visible:
                return self._handle_dialog_key(event.key)

            if event.key == pygame.K_ESCAPE:
                return "quit"

            if event.key in (pygame.K_TAB,):
                self._cycle_focus(-1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1)
                return None

            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._move_left()
                return None
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self._move_right()
                return None
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_up()
                return None
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_down()
                return None

            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate_focused()

        # Basic controller support using d-pad and common buttons.
        if event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            if hat_x < 0:
                self._move_left()
            elif hat_x > 0:
                self._move_right()
            if hat_y > 0:
                self._move_up()
            elif hat_y < 0:
                self._move_down()

        if event.type == pygame.JOYBUTTONDOWN:
            if self._dialog_visible:
                if event.button == 0:
                    self._confirm_purchase()
                elif event.button == 1:
                    self._close_dialog()
                return None

            if event.button == 0:
                return self._activate_focused()
            if event.button == 1:
                return "quit"

        return None

    def previous_car(self) -> None:
        """Navigate to the previous car and switch to Cars tab."""
        self._active_category = 0
        self._focus_zone = "cards"
        self._refresh_items()
        if not self._items:
            return
        self._selected_card_index = (self._selected_card_index - 1) % len(self._items)

    def next_car(self) -> None:
        """Navigate to the next car and switch to Cars tab."""
        self._active_category = 0
        self._focus_zone = "cards"
        self._refresh_items()
        if not self._items:
            return
        self._selected_card_index = (self._selected_card_index + 1) % len(self._items)

    def start_game(self) -> str:
        """Start the game if selected car is unlocked; otherwise show guidance."""
        selected = self.car_manager.get_selected_car()
        if not selected:
            self._push_message("Select a car before starting.")
            return "locked"

        if not self.car_manager.is_car_unlocked(selected.id):
            self._push_message(f"Need {selected.unlock_score:,} score to unlock {selected.name}.")
            return "locked"

        return "start"

    def _cycle_focus(self, direction: int) -> None:
        zones = ["tabs", "cards", "actions"]
        if self._dialog_visible:
            self._focus_zone = "dialog"
            return
        current = zones.index(self._focus_zone) if self._focus_zone in zones else 1
        self._focus_zone = zones[(current + direction) % len(zones)]

    def _move_left(self) -> None:
        if self._focus_zone == "tabs":
            self._active_category = (self._active_category - 1) % len(self.categories)
            self._refresh_items()
            return
        if self._focus_zone == "cards" and self._items:
            self._selected_card_index = max(0, self._selected_card_index - 1)
            return
        if self._focus_zone == "actions":
            self._selected_action = max(0, self._selected_action - 1)
            return
        if self._focus_zone == "dialog":
            self._dialog_action = max(0, self._dialog_action - 1)

    def _move_right(self) -> None:
        if self._focus_zone == "tabs":
            self._active_category = (self._active_category + 1) % len(self.categories)
            self._refresh_items()
            return
        if self._focus_zone == "cards" and self._items:
            self._selected_card_index = min(len(self._items) - 1, self._selected_card_index + 1)
            return
        if self._focus_zone == "actions":
            self._selected_action = min(1, self._selected_action + 1)
            return
        if self._focus_zone == "dialog":
            self._dialog_action = min(1, self._dialog_action + 1)

    def _move_up(self) -> None:
        if self._focus_zone == "actions":
            self._focus_zone = "cards"
            return

        if self._focus_zone == "cards":
            if not self._items:
                self._focus_zone = "tabs"
                return

            if self._selected_card_index >= self.GRID_COLS:
                self._selected_card_index -= self.GRID_COLS
            else:
                self._focus_zone = "tabs"
            return

    def _move_down(self) -> None:
        if self._focus_zone == "tabs":
            self._focus_zone = "cards"
            return

        if self._focus_zone == "cards":
            if not self._items:
                self._focus_zone = "actions"
                return

            next_index = self._selected_card_index + self.GRID_COLS
            if next_index < len(self._items):
                self._selected_card_index = next_index
            else:
                self._focus_zone = "actions"
            return

    def _activate_focused(self) -> Optional[str]:
        if self._focus_zone == "tabs":
            self._refresh_items()
            return None
        if self._focus_zone == "cards":
            self._activate_selected_item()
            return None
        if self._focus_zone == "actions":
            if self._selected_action == 0:
                return self.start_game()
            return "quit"
        if self._focus_zone == "dialog":
            if self._dialog_action == 0:
                self._confirm_purchase()
            else:
                self._close_dialog()
        return None

    def _activate_selected_item(self) -> None:
        if not self._items:
            return

        item = self._items[self._selected_card_index]
        if item.category == "Cars":
            if item.car_id is None:
                return
            if not self.car_manager.is_car_unlocked(item.car_id):
                self._push_message(f"Locked: reach {item.unlock_score:,} score.")
                return
            self.car_manager.select_car(item.car_id)
            self._push_message(f"Selected {item.name}.")
            return

        if item.category == "Upgrades" and self.car_manager.has_upgrade(item.id):
            self._push_message(f"{item.name} already installed.")
            return

        self._dialog_visible = True
        self._dialog_item = item
        self._dialog_action = 0
        self._focus_zone = "dialog"

    def _confirm_purchase(self) -> None:
        item = self._dialog_item
        if item is None:
            self._close_dialog()
            return

        if item.category == "Upgrades":
            success, message = self.car_manager.purchase_upgrade(item.id)
            self._push_message(message)
            self._close_dialog()
            return

        self._push_message(f"Purchased {item.name} for {item.price}.")
        self._close_dialog()

    def _close_dialog(self) -> None:
        self._dialog_visible = False
        self._dialog_item = None
        self._focus_zone = "cards"

    def _handle_dialog_click(self, pos: tuple[int, int]) -> None:
        buy_rect, cancel_rect = self._dialog_button_rects()
        if buy_rect.collidepoint(pos):
            self._dialog_action = 0
            self._confirm_purchase()
        elif cancel_rect.collidepoint(pos):
            self._dialog_action = 1
            self._close_dialog()

    def _handle_dialog_key(self, key: int) -> Optional[str]:
        if key == pygame.K_ESCAPE:
            self._close_dialog()
            return None
        if key in (pygame.K_LEFT, pygame.K_a):
            self._dialog_action = 0
            return None
        if key in (pygame.K_RIGHT, pygame.K_d):
            self._dialog_action = 1
            return None
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            if self._dialog_action == 0:
                self._confirm_purchase()
            else:
                self._close_dialog()
        return None

    def _push_message(self, text: str, duration: float = 2.1) -> None:
        self._message_text = text
        self._message_timer = duration

    def _is_item_unlocked(self, item: ShopItem) -> bool:
        if item.category != "Cars":
            return True
        if item.car_id is None:
            return True
        return self.car_manager.is_car_unlocked(item.car_id)

    def _is_item_owned(self, item: ShopItem) -> bool:
        if item.category == "Cars":
            return self._is_item_unlocked(item)
        if item.category == "Upgrades":
            return self.car_manager.has_upgrade(item.id)
        return False

    def _draw_gradient_background(self, surface: pygame.Surface) -> None:
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r = int(self.bg_top[0] + (self.bg_bottom[0] - self.bg_top[0]) * t)
            g = int(self.bg_top[1] + (self.bg_bottom[1] - self.bg_top[1]) * t)
            b = int(self.bg_top[2] + (self.bg_bottom[2] - self.bg_top[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i in range(9):
            wobble = int(18 * math.sin(self._elapsed * 1.5 + i * 0.4))
            pygame.draw.circle(
                overlay,
                (self.accent[0], self.accent[1], self.accent[2], 24),
                (140 + i * 190, 110 + (i % 3) * 90),
                42 + wobble,
                width=2,
            )
        surface.blit(overlay, (0, 0))

    def _draw_panel(self, surface: pygame.Surface, rect: pygame.Rect, fill: tuple[int, int, int], border: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, fill, rect, border_radius=16)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=16)

    def _draw_header(self, surface: pygame.Surface) -> None:
        title = self.title_font.render("RACE SHOP", True, self.text)
        subtitle = self.small_font.render("Fast picks. Quick compare. Back to racing.", True, self.muted)
        surface.blit(title, (44, 24))
        surface.blit(subtitle, (46, 76))

        balance_rect = pygame.Rect(self.width - 290, 24, 246, 74)
        self._draw_panel(surface, balance_rect, self.panel, self.accent)
        label = self.tiny_font.render("CURRENCY", True, self.muted)
        amount = self.section_font.render(f"CR {self.car_manager.credits:,}", True, self.accent_warm)
        surface.blit(label, (balance_rect.x + 16, balance_rect.y + 10))
        surface.blit(amount, (balance_rect.x + 16, balance_rect.y + 32))

    def _draw_tabs(self, surface: pygame.Surface) -> None:
        self._tab_rects.clear()
        y = 122
        tab_w = 190
        gap = 16
        start_x = 44
        for index, category in enumerate(self.categories):
            rect = pygame.Rect(start_x + index * (tab_w + gap), y, tab_w, 46)
            self._tab_rects.append(rect)
            active = index == self._active_category
            focused = self._focus_zone == "tabs" and active
            fill = (38, 56, 84) if active else (20, 30, 46)
            border = self.accent if active else (60, 79, 108)
            self._draw_panel(surface, rect, fill, border)
            if focused:
                pygame.draw.rect(surface, self.accent_warm, rect.inflate(8, 8), width=2, border_radius=18)
            label = self.body_font.render(category, True, self.text)
            surface.blit(label, label.get_rect(center=rect.center))

    def _draw_stat_bar(self, surface: pygame.Surface, x: int, y: int, label: str, value: int, color: tuple[int, int, int]) -> None:
        surface.blit(self.tiny_font.render(label, True, self.muted), (x, y))
        bar_rect = pygame.Rect(x + 42, y + 3, 108, 10)
        pygame.draw.rect(surface, (52, 66, 88), bar_rect, border_radius=5)
        fill_width = int(bar_rect.width * max(0, min(100, value)) / 100)
        pygame.draw.rect(surface, color, (bar_rect.x, bar_rect.y, fill_width, bar_rect.height), border_radius=5)

    def _draw_item_thumbnail(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect, unlocked: bool) -> None:
        thumb_h = 108 if item.premium else 76
        thumb_rect = pygame.Rect(rect.x + 12, rect.y + 12, rect.width - 24, thumb_h)

        if item.category == "Cars" and item.car_id in self._car_images:
            image = pygame.transform.smoothscale(self._car_images[item.car_id], (thumb_rect.width, thumb_rect.height))
            if not unlocked:
                dim = pygame.Surface(image.get_size(), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 120))
                image.blit(dim, (0, 0))
            surface.blit(image, thumb_rect)
        else:
            icon = pygame.Surface((thumb_rect.width, thumb_rect.height), pygame.SRCALPHA)
            base = self.accent if item.premium else (120, 154, 210)
            pygame.draw.rect(icon, (*base, 65), icon.get_rect(), border_radius=12)
            pygame.draw.rect(icon, (*base, 200), icon.get_rect(), width=2, border_radius=12)
            glyph = item.name[0].upper()
            glyph_text = self.section_font.render(glyph, True, self.text)
            icon.blit(glyph_text, glyph_text.get_rect(center=icon.get_rect().center))
            surface.blit(icon, thumb_rect)

    def _draw_badge(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect) -> None:
        badge_color = {
            "New": (92, 216, 255),
            "Hot": (255, 160, 96),
            "Limited": (255, 220, 110),
        }.get(item.badge, (140, 180, 220))
        badge_rect = pygame.Rect(rect.right - 92, rect.y + 10, 78, 24)
        pygame.draw.rect(surface, badge_color, badge_rect, border_radius=12)
        text = self.tiny_font.render(item.badge.upper(), True, (10, 18, 24))
        surface.blit(text, text.get_rect(center=badge_rect.center))

    def _draw_card(self, surface: pygame.Surface, item: ShopItem, rect: pygame.Rect, selected: bool) -> None:
        unlocked = self._is_item_unlocked(item)
        owned = self._is_item_owned(item)

        hovered = rect.collidepoint(self._mouse_pos)
        focused = self._focus_zone == "cards" and selected
        emphasis = hovered or focused

        pulse = 1.0 + 0.015 * math.sin(self._elapsed * 6.0)
        draw_rect = rect.inflate(6, 6) if emphasis else rect
        if emphasis:
            draw_rect = pygame.Rect(
                draw_rect.x,
                draw_rect.y,
                int(draw_rect.width * pulse),
                int(draw_rect.height * pulse),
            )
            draw_rect.center = rect.center

        glow = pygame.Surface((draw_rect.width + 16, draw_rect.height + 16), pygame.SRCALPHA)
        if emphasis:
            pygame.draw.rect(glow, (*self.accent, 42), glow.get_rect(), border_radius=20)
            surface.blit(glow, glow.get_rect(center=draw_rect.center))

        fill = self.card if unlocked else self.card_locked
        border = self.accent_warm if focused else ((92, 116, 155) if unlocked else (78, 86, 99))
        self._draw_panel(surface, draw_rect, fill, border)

        self._draw_item_thumbnail(surface, item, draw_rect, unlocked)
        self._draw_badge(surface, item, draw_rect)

        name_text = self.body_font.render(item.name, True, self.text if unlocked else self.muted)
        surface.blit(name_text, (draw_rect.x + 12, draw_rect.y + (126 if item.premium else 94)))

        if item.category == "Cars":
            self._draw_stat_bar(surface, draw_rect.x + 12, draw_rect.y + 152, "SPD", int(item.key_stats["speed"]), self.accent)
            self._draw_stat_bar(surface, draw_rect.x + 12, draw_rect.y + 170, "HND", int(item.key_stats["handling"]), self.good)
            self._draw_stat_bar(surface, draw_rect.x + 12, draw_rect.y + 188, "ACC", int(item.key_stats["acceleration"]), self.accent_warm)
        elif item.category == "Upgrades" and item.id in UPGRADES:
            base_stats, preview_stats = self.car_manager.get_upgrade_stat_comparison(item.id)
            comparisons = [
                ("SPD", int(base_stats.speed), int(preview_stats.speed)),
                ("ACC", int(base_stats.acceleration), int(preview_stats.acceleration)),
                ("HND", int(base_stats.handling), int(preview_stats.handling)),
                ("BRK", int(base_stats.braking), int(preview_stats.braking)),
            ]
            comparisons.sort(key=lambda entry: abs(entry[2] - entry[1]), reverse=True)

            row_y = draw_rect.y + 154
            for label, before, after in comparisons[:2]:
                comp_text = self.tiny_font.render(f"{label} {before} -> {after}", True, self.muted)
                surface.blit(comp_text, (draw_rect.x + 12, row_y))
                row_y += 18
        else:
            row_y = draw_rect.y + 156
            stat_chunks = []
            for key, value in item.key_stats.items():
                stat_chunks.append(f"{str(key)[:3].upper()} {value}")
            stats_text = self.tiny_font.render(" | ".join(stat_chunks[:2]), True, self.muted)
            surface.blit(stats_text, (draw_rect.x + 12, row_y))

        if item.category == "Cars" and not unlocked:
            price_text = self.small_font.render(f"Unlock @ {item.unlock_score:,}", True, self.danger)
        elif owned:
            price_text = self.small_font.render("OWNED", True, self.good)
        else:
            price_text = self.small_font.render(f"CR {item.price:,}", True, self.accent_warm)
        surface.blit(price_text, (draw_rect.x + 12, draw_rect.bottom - 26))

    def _draw_grid(self, surface: pygame.Surface) -> None:
        self.card_rects.clear()

        cols = self.GRID_COLS
        gap_x = 16
        gap_y = 16
        margin_x = 44
        top = 186
        card_w = (self.width - margin_x * 2 - gap_x * (cols - 1)) // cols
        card_h = 228

        for index, item in enumerate(self._items):
            row = index // cols
            col = index % cols
            rect = pygame.Rect(margin_x + col * (card_w + gap_x), top + row * (card_h + gap_y), card_w, card_h)
            self.card_rects.append(rect)
            self._draw_card(surface, item, rect, index == self._selected_card_index)

    def _draw_actions(self, surface: pygame.Surface) -> None:
        self._action_rects.clear()
        y = self.height - 86
        start_rect = pygame.Rect(self.width // 2 - 190, y, 170, 48)
        back_rect = pygame.Rect(self.width // 2 + 20, y, 170, 48)
        self._action_rects.extend([start_rect, back_rect])

        start_focus = self._focus_zone == "actions" and self._selected_action == 0
        back_focus = self._focus_zone == "actions" and self._selected_action == 1

        self._draw_panel(surface, start_rect, (24, 82, 66), self.accent if start_focus else (72, 178, 146))
        self._draw_panel(surface, back_rect, (42, 50, 66), self.accent if back_focus else (86, 98, 122))

        start_label = self.body_font.render("START RACE", True, self.text)
        back_label = self.body_font.render("BACK", True, self.text)
        surface.blit(start_label, start_label.get_rect(center=start_rect.center))
        surface.blit(back_label, back_label.get_rect(center=back_rect.center))

        hint = self.tiny_font.render("Tab/Arrows/Enter supported for keyboard and controller.", True, self.muted)
        surface.blit(hint, (44, y + 56))

    def _dialog_button_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        buy = pygame.Rect(self.width // 2 - 152, self.height // 2 + 52, 132, 44)
        cancel = pygame.Rect(self.width // 2 + 20, self.height // 2 + 52, 132, 44)
        return buy, cancel

    def _draw_dialog(self, surface: pygame.Surface) -> None:
        if not self._dialog_visible or self._dialog_item is None:
            return

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        rect = pygame.Rect(self.width // 2 - 220, self.height // 2 - 110, 440, 220)
        self._draw_panel(surface, rect, self.panel, self.accent)

        title = self.section_font.render("Confirm Purchase", True, self.text)
        message = self.small_font.render(f"Buy {self._dialog_item.name} for CR {self._dialog_item.price:,}?", True, self.muted)
        surface.blit(title, (rect.x + 20, rect.y + 20))
        surface.blit(message, (rect.x + 20, rect.y + 72))

        buy_rect, cancel_rect = self._dialog_button_rects()
        buy_focus = self._focus_zone == "dialog" and self._dialog_action == 0
        cancel_focus = self._focus_zone == "dialog" and self._dialog_action == 1

        self._draw_panel(surface, buy_rect, (28, 98, 76), self.accent_warm if buy_focus else (82, 201, 162))
        self._draw_panel(surface, cancel_rect, (68, 48, 48), self.accent_warm if cancel_focus else (180, 102, 102))

        buy_text = self.body_font.render("BUY", True, self.text)
        cancel_text = self.body_font.render("CANCEL", True, self.text)
        surface.blit(buy_text, buy_text.get_rect(center=buy_rect.center))
        surface.blit(cancel_text, cancel_text.get_rect(center=cancel_rect.center))

    def _draw_message(self, surface: pygame.Surface) -> None:
        if not self._message_text:
            return

        alpha = int(255 * min(1.0, self._message_timer / 2.1))
        banner = pygame.Surface((560, 44), pygame.SRCALPHA)
        pygame.draw.rect(banner, (14, 20, 30, 224), banner.get_rect(), border_radius=12)
        pygame.draw.rect(banner, (*self.accent, 255), banner.get_rect(), width=2, border_radius=12)
        text = self.small_font.render(self._message_text, True, self.text)
        banner.blit(text, text.get_rect(center=banner.get_rect().center))
        banner.set_alpha(alpha)
        surface.blit(banner, banner.get_rect(center=(self.width // 2, self.height - 130)))

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_gradient_background(surface)
        self._draw_header(surface)
        self._draw_tabs(surface)
        self._draw_grid(surface)
        self._draw_actions(surface)
        self._draw_message(surface)
        self._draw_dialog(surface)




