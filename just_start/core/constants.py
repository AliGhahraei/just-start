from os.path import expanduser, join
from os import getenv

CONFIG_DIR = join(getenv('XDG_CONFIG_HOME', expanduser(join('~', '.config'))),
                  'just-start')
LOCAL_DIR = join(getenv('XDG_DATA_HOME',
                        expanduser(join('~', '.local', 'share'))),
                 'just-start')

CONFIG_PATH = join(CONFIG_DIR, 'preferences.yml')
LOG_PATH = join(LOCAL_DIR, 'log')

HELP_MESSAGE = ('(a)dd task, (c)omplete task, (d)elete task, (h)elp, s(k)ip to'
                ' another pomodoro phase, (l)ocation change, (m)odify task,'
                ' (p)omodoro pause/resume, (q)uit, (r)efresh tasks, (s)top'
                ' pomodoro, s(y)nc server, (!) custom command')

PHASE_SKIP_PROMPT = 'Enter how many phases you want to skip'
SYNC_MSG = 'Syncing task server...'
