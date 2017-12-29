# Text Styles
BOLD = '\x1b[1m'
ITALIC = '\x1b[3m'
UNDERLINE = '\x1b[4m'

# Bright Colours
RED = '\x1b[91m'
GREEN = '\x1b[92m'
YELLOW = '\x1b[93m'
BLUE = '\x1b[94m'
PURPLE = '\x1b[95m'
CYAN = '\x1b[96m'
WHITE = '\x1b[97m'
ENDC = '\x1b[0m'

# Other Escape Sequences
CLEAR_LINE = '\x1b[0K'
HIDE_CURSOR = '\x1b[?25l'
SHOW_CURSOR = '\x1b[?25h'


def move_up(num_lines):
    return f'\033[{num_lines}A' if num_lines else ''


def move_down(num_lines):
    return f'\033[{num_lines}B' if num_lines else ''


def move_forward(num_columns):
    return f'\033[{num_columns}C' if num_columns else ''


def move_backward(num_columns):
    return f'\033[{num_columns}D' if num_columns else ''
