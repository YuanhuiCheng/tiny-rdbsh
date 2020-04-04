from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from sqlutil import SQLUtil


work_dir = '/'

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

sqlutil = SQLUtil()

while True:
    text = prompt(work_dir + ' > $ ')
    args = text.split(' ')

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
                print('cd: no such directory: %s', work_dir)

    elif args[0].startswith('path'):
        # path maintanence
        path = sqlutil.path_var()
        print(':'.join(path))

    elif args[0].startswith('find'):
        if args[1].startswith('/'):
            path = args[1]
        else:
            path = simplify_path(work_dir + '/' + args[1])
        files = sqlutil.find(path, args[2:])
        for file in files:
            file.fprint(work_dir)

    elif args[0].startswith('grep'):
        if args[1].startswith('/'):
            file_abspath= args[2]
        else:
            file_abspath = simplify_path(work_dir + '/' + args[2])
        files = sqlutil.grep(args[1], file_abspath)
        for file in files:
            file.gprint(args[1])

    elif args[0].startswith('q'):
        print("Goodbye!")
        break
        
    else:  
        # execute executable functions 
        exec_exists = sqlutil.get_executable(args)




        