from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from sqlutil import SQLUtil


work_dir = '/'

allowed_commands = ('ls', 'cd', 'find', 'grep', 'path')


def simplify_path(path):
    ''' Simplify . // and .. in path '''
    stack = []
    for p in path.split("/"):
        if p == "..":
            if stack:
                stack.pop()
        elif p and p != '.':
            stack.append(p)
    return '/' + '/'.join(stack)


def is_valid_input(text):
    if not text in allowed_commands:
        return False
    else:
        return True

sqlutil = SQLUtil()

while True:
    text = prompt(work_dir + ' > $ ')
    args = text.split(' ')

    if not is_valid_input(args[0]):
        print('Command not supported. Valid commands are: ' + ' '.join(allowed_commands))

    if args[0].startswith('ls'):
        prop = False
        path = ''
        index_arg = 1

        if len(args) > 1:
            if args[1] == '-l':
                prop = True
                index_arg += 1

        # if equal no path argument
        if index_arg == len(args):
            path = work_dir
        else:
            if args[index_arg].startswith('/'):
                path = args[index_arg]
            else:
                path = work_dir + '/' + args[index_arg]

        files = sqlutil.ls(simplify_path(path), prop)
        for file in files:
            if not prop:
                print(file.name)
            else:
                # print('fuck')
                file.lprint()
    elif args[0].startswith('cd'):
        if len(args) == 1:
            work_dir = '/'
        else:
            if args[1].startswith('/'):
                temp_work_dir = args[1]
            else:
                temp_work_dir = simplify_path(work_dir + '/' + args[1])
            if sqlutil.check_path_exists(temp_work_dir, 'd'):
                work_dir = temp_work_dir
            else:
                print('cd: no such file or directory: %s', temp_work_dir)
    elif args[0].startswith('path'):
        sqlutil.path_var();
    else:   
        exec_exists = sqlutil.get_executable(args[0])




        