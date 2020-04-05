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

    # $PATH gives all the path variable
    elif args[0].startswith('$PATH'):
        path = sqlutil.get_path_var()
        print(':'.join(path))
    #PATH=$PATH:~/opt/bin add ~/opt/bin as a path variable
    elif args[0].startswith('PATH'):
        paths = args[0].split("=")[1].split(":")
        last_flag = 0 # check if the new path should be insert at last or first
        new_path = None
        if paths[0] == "$PATH":
            last_flag = 1
            new_path = paths[1]
        else:
            new_path = paths[0]
        sqlutil.update_path_var(new_path, last_flag)

    elif args[0].startswith('find'):
        # set absolute path
        if args[1].startswith('/'):
            path = args[1]
        else:
            path = simplify_path(work_dir + '/' + args[1])
        # set options arguments
        name = user = inodeNum = linkNum = None
        options = args[2:]
        for i in range(len(options)):
            if options[i] == '-name':
                i = i + 1
                name = options[i]
            elif options[i] == '-user':
                i = i + 1
                user = options[i]
            elif options[i] == '-inum':
                i = i + 1
                inodeNum = options[i]
            elif options[i] == '-links':
                i = i + 1
                linkNum = options[i]
        # Call sqlUtil to get all the files that match the contidions
        files = sqlutil.find(path, name, user, inodeNum, linkNum)
        # Pretty print all the info
        for file in files:
            file.fprint(work_dir)

    elif args[0].startswith('grep'):
        if args[2].startswith('/'):
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




        