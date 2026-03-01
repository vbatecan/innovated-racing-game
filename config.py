CAM_X_SIZE = 640
CAM_Y_SIZE = 480
WINDOW_SIZE = {"width": 1920, "height": 1080}

ROAD_SIZE = {"width": 700, "height": 1080}
LANE_COUNT = 3
MIN_LANE_COUNT = 1
MAX_LANE_COUNT = 6

SHOW_CAMERA = False

FONT_SIZE = 24
CAR_SPEED = 10
MAX_FPS = 60
OBSTACLE_FREQUENCY = 1  # Per Max FPS
STEERING_SENSITIVITY = 1.0
AVAILABLE_FPS = [30, 60, 120]

# Physics settings
ACCELERATION = 0.1
FRICTION = 0.01
BRAKE_STRENGTH = 0.25
BRAKE_SENSITIVITY = 5
TURN_STEER_SENS = 30

# Traffic vehicle scaling
TRAFFIC_LANE_WIDTH_RATIO = 0.28
TRAFFIC_MIN_SIZE = 20
TRAFFIC_MAX_SOURCE_SCALE = 0.75

# Road crack hazards
CRACK_SPAWN_FREQUENCY = 300
MAX_CRACKS = 2
CRACK_LANE_WIDTH_RATIO = 0.30

# BR hazards
BR_SPAWN_FREQUENCY = 260
MAX_BRS = 2
BR_LANE_WIDTH_RATIO = 0.75

# Oil spill hazards
OIL_SPILL_SPAWN_FREQUENCY = 340
MAX_OIL_SPILLS = 2
OIL_SPILL_LANE_WIDTH_RATIO = 0.65
OIL_SWERVE_DURATION_MS = 3000
OIL_SWERVE_STRENGTH = 1.2
OIL_SWERVE_FREQUENCY = 0.03

# Maps
MAP_SWITCH_SCORE = 500
ROAD_LINE_BORDER_WIDTH = 0

# Player life system
STARTING_LIVES = 5
MAX_HEARTS = 5

SETTING_OPTIONS = [
    "Car Speed",
    "Max FPS",
    "Show Camera",
    "Obstacle Freq",
    "Lane Count",
    "Sensitivity",
    "Brake Sens",
]

HAND_CONNECTIONS = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (5, 9),
    (9, 13),
    (13, 17),
)
