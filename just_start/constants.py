from os import getenv
from os.path import expanduser, join, dirname

LOCAL_DIR = join(getenv('XDG_DATA_HOME',
                        expanduser(join('~', '.local', 'share'))),
                 'just-start')
CONFIG_DIR = join(getenv('XDG_CONFIG_HOME', expanduser(join('~', '.config'))),
                  'just-start')
CONFIG_PATH = join(CONFIG_DIR, 'preferences.toml')
LOG_PATH = join(LOCAL_DIR, 'log')
PERSISTENT_PATH = join(LOCAL_DIR, 'db')
SCHEMA_PATH = join(dirname(__file__), 'preferences.schema.json')

KEYBOARD_HELP = ('(a)dd task, (c)omplete task, (d)elete task, (h)elp, (s)kip to'
                 ' another pomodoro phase, (l)ocation change, (m)odify task,'
                 ' (p)omodoro pause/resume, (q)uit, (r)efresh tasks, s(t)op'
                 ' pomodoro, s(y)nc server, (!) custom command')

PHASE_SKIP_PROMPT = 'Enter how many phases you want to skip'
SYNC_MSG = 'Syncing task server...'
ACTION_PROMPT = 'Enter your action'
SKIPPED_PHASES_PROMPT = 'How many phases do you want to skip?'
TASK_IDS_PROMPT = "Enter the tasks' ids"
ADD_PROMPT = "Enter the task's data"
MODIFY_PROMPT = "Enter the modified tasks' data"
LOCATION_CHANGE_PROMPT = "Enter 'w' for work or anything else for home"
CUSTOM_COMMAND_PROMPT = 'Enter your custom command'
EXIT_MESSAGE = 'Exiting...'

INVALID_ACTION_KEY = 'Invalid action key'
EMPTY_STRING = 'An empty string is not allowed'
UNHANDLED_ERROR = f'Unhandled error: please see ({LOG_PATH})'

SKIP_NOT_ENABLED = 'Sorry, please work 1 pomodoro to re-enable phase skipping'
INVALID_PHASE_NUMBER = 'Number of phases must be positive'
LONG_BREAK_SKIP_NOT_ENABLED = "Skip to a long break is not allowed"

ERRORS = {INVALID_ACTION_KEY, EMPTY_STRING, UNHANDLED_ERROR, SKIP_NOT_ENABLED,
          INVALID_PHASE_NUMBER, LONG_BREAK_SKIP_NOT_ENABLED}

STOP_MESSAGE = 'Pomodoro timer stopped'

SKIP_ENABLED = 'skip_enabled'

RECURRENCE_OFF = 'rc.recurrence.confirmation=off'
CONFIRMATION_OFF = 'rc.confirmation=off'
