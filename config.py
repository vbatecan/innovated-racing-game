CAM_X_SIZE = 640
CAM_Y_SIZE = 480
WINDOW_SIZE = {"width": 1920, "height": 1080}

ROAD_SIZE = {"width": 700, "height": 1080}
LANE_COUNT = 3
MIN_LANE_COUNT = 1
MAX_LANE_COUNT = 6

SHOW_CAMERA = True
DEBUG_PERF = False

FONT_SIZE = 24
CAR_SPEED = 25
MAX_CAR_SPEED = 30
MAX_FPS = 60
OBSTACLE_FREQUENCY = 1
STEERING_SENSITIVITY = 1.0
AVAILABLE_FPS = [30, 60, 120]

ACCELERATION = 0.1
FRICTION = 0.01
BRAKE_STRENGTH = 0.25
BRAKE_SENSITIVITY = 5
TURN_STEER_SENS = 30
BRAKE_HAZARD_FREEZE_MS = 0

TRAFFIC_LANE_WIDTH_RATIO = 0.28
TRAFFIC_MIN_SIZE = 20
TRAFFIC_MAX_SOURCE_SCALE = 0.75

CRACK_SPAWN_FREQUENCY = 300
MAX_CRACKS = 2
CRACK_LANE_WIDTH_RATIO = 0.30

BR_SPAWN_FREQUENCY = 260
MAX_BRS = 2
BR_LANE_WIDTH_RATIO = 0.75

OIL_SPILL_SPAWN_FREQUENCY = 340
MAX_OIL_SPILLS = 1
OIL_SPILL_LANE_WIDTH_RATIO = 0.65
OIL_SWERVE_DURATION_MS = 1500
OIL_SWERVE_STRENGTH = 1.2
OIL_SWERVE_FREQUENCY = 0.5

MAP_SWITCH_SCORE = 1000
MAP_TRANSITION_DISTANCE = 1400
ROAD_LINE_BORDER_WIDTH = 1
MAP_BORDER_OVERRIDES = {
    "city_roadfinal.png": {"left_ratio": 0.37, "right_ratio": 0.63},
    "dessert upt2.png": {"left_ratio": 0.37, "right_ratio": 0.63},
    "dessert upt3.png": {"left_ratio": 0.37, "right_ratio": 0.63},
    "highway.png": {"left_ratio": 0.37, "right_ratio": 0.63},
}

STARTING_LIVES = 3
MAX_HEARTS = STARTING_LIVES

TRUE_FALSE_QUESTIONS = [
    {
        "prompt": "A data structure is used to organize and store data.",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "An array can store multiple values.",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "A stack follows LIFO (Last In, First Out).",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "A queue follows FIFO (First In, First Out).",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "A linked list is a linear data structure.",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "A variable can hold multiple values at the same time.",
        "answer": False,
        "difficulty": "EASY",
    },
    {
        "prompt": "A list in Python can store both numbers and strings.",
        "answer": True,
        "difficulty": "EASY",
    },
    {
        "prompt": "A binary tree can have at most three children per node.",
        "answer": False,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "A hash table uses key-value pairs for data storage.",
        "answer": True,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "Binary search requires a sorted array to work correctly.",
        "answer": True,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "A graph can contain cycles.",
        "answer": True,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "Recursion is a function that calls itself.",
        "answer": True,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "In a binary search tree, all values in the left subtree are greater than the root.",
        "answer": False,
        "difficulty": "MEDIUM",
    },
    {
        "prompt": "The time complexity of binary search is O(log n).",
        "answer": True,
        "difficulty": "HARD",
    },
    {
        "prompt": "Bubble sort is the fastest sorting algorithm.",
        "answer": False,
        "difficulty": "HARD",
    },
    {
        "prompt": "A depth-first search uses a stack data structure.",
        "answer": True,
        "difficulty": "HARD",
    },
    {
        "prompt": "A breadth-first search uses a queue data structure.",
        "answer": True,
        "difficulty": "HARD",
    },
    {
        "prompt": "Dijkstra's algorithm can correctly find shortest paths with negative edge weights.",
        "answer": False,
        "difficulty": "HARD",
    },
]

MULTIPLE_CHOICE_QUESTIONS = []

SETTING_OPTIONS = [
    "Car ",
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

SCORING_CONFIG = {
    "base_points_per_distance": 1.0,
    "top__bonus": 0,
    "accel_bonus": 0,
    "clean_drive_bonus": 0,
    "clean_drive_interval": 40000,
    "near_miss_bonus": 0,
    "sharp_turn_bonus": 0,
}


