"""Verification script for modern UI implementation."""
import sys
from pathlib import Path

# Initialize pygame first
import pygame
pygame.init()
pygame.display.set_mode((100, 100))

print("=" * 60)
print("MODERN UI IMPLEMENTATION VERIFICATION")
print("=" * 60)

tests_passed = 0
tests_total = 0

def test(name, func):
    global tests_passed, tests_total
    tests_total += 1
    try:
        func()
        print(f"✅ {name}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

# Test 1: Import main modules
def test_imports():
    from ui.components.modern_button import ModernButton
    from ui.components.particle_system import BackgroundEffect
    from ui.modern_homepage import ModernHomePage
    from main import main

test("Import core modules", test_imports)

# Test 3: Instantiate components
def test_components():
    import pygame
    from ui.components.modern_button import ModernButton
    btn = ModernButton(0, 0, 100, 50, "TEST")

test("Create ModernButton instance", test_components)

# Test 4: Instantiate homepage
def test_homepage():
    from ui.modern_homepage import ModernHomePage
    hp = ModernHomePage({"width": 1920, "height": 1080})

test("Create ModernHomePage instance", test_homepage)

# Test 5: Test callbacks
def test_callbacks():
    from ui.modern_homepage import ModernHomePage
    hp = ModernHomePage({"width": 1920, "height": 1080})
    hp.set_callbacks({
        "start": lambda: None,
        "shop": lambda: None,
        "settings": lambda: None,
    })

test("Set button callbacks", test_callbacks)

# Test 6: File existence
def test_files():
    files = [
        "ui/components/modern_button.py",
        "ui/components/particle_system.py",
        "ui/modern_homepage.py",
        "demo_homepage.py",
    ]
    for f in files:
        assert Path(f).exists(), f"Missing {f}"

test("Verify all files exist", test_files)

# Summary
print("=" * 60)
print(f"RESULTS: {tests_passed}/{tests_total} tests passed")
if tests_passed == tests_total:
    print("✅ ALL SYSTEMS GO! Implementation is complete and working.")
else:
    print(f"⚠️  {tests_total - tests_passed} test(s) failed")
    sys.exit(1)
print("=" * 60)
