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

KEYBOARD_HELP = ('(a)dd task, (c)omplete task, (d)elete task, (h)elp, (m)odify task,'
                 ' (p)omodoro pause/resume, (q)uit, (r)efresh tasks, (s)top pomodoro,'
                 ' s(y)nc server, (!) custom command')

ACTION_PROMPT = 'Enter your action'
TASK_IDS_PROMPT = "Enter the tasks' ids"
ADD_PROMPT = "Enter the task's data"
MODIFY_PROMPT = "Enter the modified tasks' data"
CUSTOM_COMMAND_PROMPT = 'Enter your custom command'

INVALID_ACTION_KEY = 'Invalid action key'
EMPTY_STRING = 'An empty string is not allowed'
UNHANDLED_ERROR = 'Unhandled error'
UNHANDLED_ERROR_MESSAGE_WITH_LOG_PATH = (f'{UNHANDLED_ERROR}, please see {LOG_PATH} and/or contact'
                                         f' the author')

STOP_MESSAGE = 'Pomodoro timer stopped'

RECURRENCE_OFF = 'rc.recurrence.confirmation=off'
CONFIRMATION_OFF = 'rc.confirmation=off'
