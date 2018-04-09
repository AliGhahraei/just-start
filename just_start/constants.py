from os import getenv
from os.path import expanduser, join

LOCAL_DIR = join(getenv('XDG_DATA_HOME',
                        expanduser(join('~', '.local', 'share'))),
                 'just-start')
CONFIG_DIR = join(getenv('XDG_CONFIG_HOME', expanduser(join('~', '.config'))),
                  'just-start')
CONFIG_PATH = join(CONFIG_DIR, 'preferences.toml')
LOG_PATH = join(LOCAL_DIR, 'log')
PERSISTENT_PATH = join(LOCAL_DIR, 'db')

# noinspection SpellCheckingInspection
KEYBOARD_HELP = ('(a)dd task, (c)omplete task, (d)elete task, (h)elp, s(k)ip to'
                 ' another pomodoro phase, (l)ocation change, (m)odify task,'
                 ' (p)omodoro pause/resume, (q)uit, (r)efresh tasks, (s)top'
                 ' pomodoro, s(y)nc server, (!) custom command')

PHASE_SKIP_PROMPT = 'Enter how many phases you want to skip'
SYNC_MSG = 'Syncing task server...'
KEYBOARD_INTERRUPT_ERROR = ('Ctrl+C before selecting an action. If you wanted'
                            ' to quit, use q instead')
EMPTY_STRING = 'An empty string is not allowed'
ACTION_PROMPT = 'Enter your action'
INVALID_ACTION_KEY = 'Invalid action key'
SKIPPED_PHASES_PROMPT = 'How many phases do you want to skip?'

RECURRENCE_OFF = 'rc.recurrence.confirmation=off'
CONFIRMATION_OFF = 'rc.confirmation=off'
