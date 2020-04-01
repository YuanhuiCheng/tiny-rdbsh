import os
import sys
from stat import *
import grp
import pwd
import csv
import re
from pathlib import Path

# 'file' attributes
# file_attr = ['id', 'inode', 'dev', 'type', 'op', 'gp', 'tp', 'num_of_links', 
#     'owner_id', 'group_id', 'size', 'time', 'name', 'parentID', 'abs_path']
# may remove the 'name' and 'pid' columns
file_attr = ['fid', 'inode', 'ftype', 'op', 'gp', 'tp', 'numoflinks', 
    'uid', 'size', 'ctime', 'mtime', 'name', 'pid', 'abspath']

# 'fileType' table
# file_type_attr = ['id', 'type']
# file_type_dic = {
#     'd' : 'Directory',
#     '-' : 'Regular',
#     'l' : 'Symoblic link',
#     'c' : 'Character special',
#     'b' : 'Block special',
#     'p' : 'FIFO',
#     's' : 'Socket',
#     'do' : 'Door',
#     'ep' : 'Event port',
#     'wo' : 'Whiteout'
# }

# 'permissionType' table
# permission_type_attr = ['id', 'pr', 'pw', 'pe']
# permission_type_dic = {
#     0 : ['-', '-', '-'],
#     1 : ['-', '-', 'x'],
#     2 : ['-', 'w', '-'],
#     3 : ['-', 'w', 'x'],
#     4 : ['r', '-', '-'],
#     5 : ['r', '-', 'x'],
#     6 : ['r', 'w', '-'],
#     7 : ['r', 'w', 'x']
# }

# 'user' attributes
# may remove 'path' column
# user_attr = ['uid', 'name', 'path', 'gid']
user_attr = ['uid', 'name', 'gid']

# 'group' attributes
group_attr = ['gid', 'name']

# 'pathVar' attributes
# path_var_attr = ['var', 'path', 'fileID']
path_attr = ['fid']

# 'symbolicLink' attributes
sym_link_attr = ['fid', 'pfid']
sym_pointed_file_by_file = {}

# 'hardLink' attributes
hard_link_attr = ['inode', 'dev']
inode_dev_lst = []

d_file_cnt = 0
r_file_cnt = 0
l_file_cnt = 0
c_file_cnt = 0
b_file_cnt = 0
p_file_cnt = 0
s_file_cnt = 0
do_file_cnt = 0
ep_file_cnt = 0
wo_file_cnt = 0

cnt_by_extension = {}
regular_file_fake_path = []

def analyze_attr(file_path, skipped_file):
    global d_file_cnt
    global r_file_cnt
    global l_file_cnt
    global c_file_cnt
    global b_file_cnt
    global p_file_cnt
    global s_file_cnt
    global do_file_cnt
    global ep_file_cnt
    global wo_file_cnt
        
    info = os.stat(file_path, follow_symlinks=False)
    mode = info.st_mode

    inode = ''
    dev = ''
    file_type = ''
    op = ''
    gp = ''
    tp = ''
    num_of_links = ''
    owner_id = ''
    group_id = ''
    size = ''
    time = ''

    # get inode number
    inode = info.st_ino
    
    '''
    for testing: add an attribute called 'dev'
    '''
    dev = info.st_dev

    if [inode, dev] not in inode_dev_lst:
        inode_dev_lst.append([inode, dev])

    # get file type    
    file_type = ''
    pointed_file = ''

    if S_ISDIR(mode):
        file_type = 'd'
        d_file_cnt+=1
    elif S_ISREG(mode):
        file_type = '-'
        r_file_cnt+=1
        if file_path not in regular_file_fake_path:
            fake_file_path = 'temp_unix' + str(file_path)
            regular_file_fake_path.append(fake_file_path)
    elif S_ISLNK(mode):
        file_type = 'l'
 
        pointed_file_path = os.readlink(file_path)
        parent_level_cnt = pointed_file_path.count('../')
        formal_pointed_file_path = ''
        
        partial_pointed_file_path = pointed_file_path.replace('../', '')
        formal_pointed_file_path = os.path.join(Path(file_path).parents[parent_level_cnt], partial_pointed_file_path)
        formal_pointed_file_path = os.path.normpath(formal_pointed_file_path)

        if file_path in sym_pointed_file_by_file:
            print(file_path + ' is already pointed to ' + sym_pointed_file_by_file[file_path])
        else:
            sym_pointed_file_by_file[file_path] = formal_pointed_file_path
        
        l_file_cnt+=1
        
    elif S_ISCHR(mode):
        file_type = 'c'
        c_file_cnt+=1
        print('char special file: ' + str(file_path))
    elif S_ISBLK(mode):
        file_type = 'b'
        b_file_cnt+=1
    elif S_ISFIFO(mode):
        file_type = 'p'
        p_file_cnt+=1
    elif S_ISSOCK(mode):
        file_type = 's'
        s_file_cnt+=1
    elif S_ISDOOR(mode): # from a door
        file_type = 'do'
        do_file_cnt+=1
    elif S_ISPORT(mode): # from an event port
        file_type = 'ep'
        ep_file_cnt+=1
    elif S_ISWHT(mode): # from a whiteout
        file_type = 'wo'
        wo_file_cnt+=1
    else:
        print('cannot determine the type of file: ' + str(file_path) 
            + ' mode: ' + str(stat.filemode(mode)))
    
    '''
    looks like there is no 'network file' (maybe it doesn't matter)
    '''

    # get permissions
    op = 0
    gp = 0
    tp = 0

    # get owner permission
    if mode & S_IRUSR: # read permission
        op+=4
    if mode & S_IWUSR: # write permission
        op+=2
    if mode & S_IXUSR: # execute permission
        op+=1
    
    # get group permission
    if mode & S_IRGRP: # read permission
        gp+=4
    if mode & S_IWGRP: # write permission
        gp+=2
    if mode & S_IXGRP: # execute permission
        gp+=1

    # get others permission
    if mode & S_IROTH: # read permission
        tp+=4
    if mode & S_IWOTH: # write permission
        tp+=2
    if mode & S_IXOTH: # execute permission
        tp+=1

    # get number of links
    num_of_links = info.st_nlink

    # get owner id
    owner_id = info.st_uid

    # get group id
    group_id = info.st_gid

    # get file size
    size = info.st_size

    # get creation time or modification time 
    ctime = info.st_ctime

    # get modification time 
    mtime = info.st_mtime

    # get file extension
    ext = Path(file_path).suffix
    # if ext == '':
    #     print('no suffix file: ' + str(file_path))
    if ext in cnt_by_extension:
        cnt_by_extension[ext] = cnt_by_extension[ext]+1
    else:
        cnt_by_extension[ext] = 1

    return [inode, file_type, op, gp, tp, num_of_links, owner_id, size, ctime, mtime]
    # file_attr = ['fid', 'inode', 'ftype', 'op', 'gp', 'tp', 'numoflinks', 
    # 'uid', 'size', 'ctime', 'mtime', 'name', 'pid', 'abspath']

def main():
    print ("\n\n=====================================")
    print ("ece356 project: UNIX dumb file system")
    print ("=====================================\n\n")

    file_by_path = {}

    walk_dir = sys.argv[1]
    walk_dir_name = os.path.basename(walk_dir)
    walk_dir_abs_path = os.path.abspath(walk_dir)

    skipped_file = 'err/skipped_info.txt'
    os.makedirs(os.path.dirname(skipped_file), exist_ok=True)

    skipped_file = open(skipped_file, 'w')

    root_att_lst = analyze_attr(walk_dir_abs_path, skipped_file)
    root_att_lst.insert(0, 1)
    root_att_lst.append('') # name of super root, given as empty string
    root_att_lst.append(0)

    file_by_path[walk_dir_abs_path] = root_att_lst
    print('walk_dir: ' + str(walk_dir_abs_path) + ' |walk_dir_att: ' + str(file_by_path[walk_dir_abs_path]))

    file_id = 1

    for root, subdirs, files in os.walk(walk_dir):
        '''
        may change it later
        ''' 

        if re.match('/proc*', root) or re.match('/sys*', root):
            skipped_file.write('skip file (root): ' + root + '\n')
            continue

        parent_id = -1
        root_name = os.path.basename(root)

        file_tuple = file_by_path[root]
        parent_id = file_tuple[0]
    
        for subdir in subdirs:
            sub_dir_path = os.path.join(root, subdir)

            '''
            may change it later
            ''' 

            sub_dir_name = os.path.basename(subdir)

            file_id += 1

            rst_attr_lst = [file_id]
            att_lst = analyze_attr(sub_dir_path, skipped_file)
            if att_lst is None: 
                print('skip symlink dir: ' + sub_dir_path)
                continue
            rst_attr_lst.extend(att_lst)
            rst_attr_lst.append(sub_dir_name)
            rst_attr_lst.append(parent_id)

            file_by_path[sub_dir_path] = rst_attr_lst

        for filename in files:
            file_id += 1
            file_path = os.path.join(root, filename)

            att_lst = analyze_attr(file_path, skipped_file)
            if att_lst is None:
                skipped_file.write('skip file (file): ' + file_path + '\n')
                continue

            file_by_path[file_path] = [file_id, filename, parent_id]
            rst_attr_lst = [file_id]

            rst_attr_lst.extend(att_lst)
            rst_attr_lst.append(filename)
            rst_attr_lst.append(parent_id)

            file_by_path[file_path] = rst_attr_lst
    
    os.makedirs('csv', exist_ok=True)
        
    with open('csv/file_t.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        writer.writerow(file_attr)
        for key, value in file_by_path.items():
            value.append(key)
            writer.writerow(value)
    
    # with open('csv/fileType_t.csv', 'w+') as w_csv:
    #     writer = csv.writer(w_csv)
    #     writer.writerow(file_type_attr)
    #     for key, value in file_type_dic.items():
    #         writer.writerow([key, value])
    
    # with open('csv/permissionType_t.csv', 'w+') as w_csv:
    #     writer = csv.writer(w_csv)
    #     writer.writerow(permission_type_attr)
    #     for key, value in permission_type_dic.items():
    #         value.insert(0, key)
    #         writer.writerow(value)

    with open('csv/group_t.csv', 'w+') as group_csv, open('csv/user_t.csv', 'w+') as user_csv:
        group_writer = csv.writer(group_csv)
        group_writer.writerow(group_attr)

        user_writer = csv.writer(user_csv)
        user_writer.writerow(user_attr)

        # group_entries = grp.getgrall()

        # for group_entry in group_entries:
        #     group_writer.writerow([group_entry.gr_gid, group_entry.gr_name])
            
        #     print('group is: ' + str(group_entry.gr_name))
        #     for mem in group_entry.gr_mem:
        #         print('mem is: ' + str(mem))
        #         user_writer.writerow([pwd.getpwnam(mem), mem, group_entry.gr_gid])

        pwd_entries = pwd.getpwall()

        group_id_lst = []

        for pwd_entry in pwd_entries:
            # user_writer.writerow([pwd_entry.pw_uid, pwd_entry.pw_name, pwd_entry.pw_dir, pwd_entry.pw_gid])
            user_writer.writerow([pwd_entry.pw_uid, pwd_entry.pw_name, pwd_entry.pw_gid])

            if pwd_entry.pw_gid not in group_id_lst:
                group_id_lst.append(pwd_entry.pw_gid)
                try:
                    group_writer.writerow([pwd_entry.pw_gid, grp.getgrgid(pwd_entry.pw_gid).gr_name])
                except KeyError:
                    print('--\n no group name attributed for group id ' + str(pwd_entry.pw_gid))
                    print('pwd entry: ' + str(pwd_entry) + '\n--')

    with open('csv/pathVar_t.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        writer.writerow(path_attr)
        for key, value in os.environ.items():
            if key == 'PATH':
                paths = [v.strip() for v in value.split(':')]
                for i in range(len(paths)):
                    var_name = 'PATH'+str(i+1)
                    path = paths[i]
                    file_property = file_by_path[path]
                    file_ID = file_property[file_attr.index('fid')]
                    # writer.writerow([var_name, path, file_ID])
                    writer.writerow([file_ID])
            # else:
            #     try:
            #         file_property = file_by_path[value]
            #         file_ID = file_property[file_attr.index('id')]
            #         writer.writerow([key, value, file_ID])
            #     except:
            #         print('may not be a regular executable var: ' + str(key) + ' => ' + str(value))
                    
                    
    with open('csv/symbolicLink_t.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        # sym_link_attr.extend(['filePath', 'pointedFilePath'])
        writer.writerow(sym_link_attr)
        for key, value in sym_pointed_file_by_file.items():
            try:
                file_property = file_by_path[key]
                pointed_file_property = file_by_path[value]
                file_ID = file_property[file_attr.index('fid')]
                pointed_file_ID = pointed_file_property[file_attr.index('fid')]
                # writer.writerow([file_ID, pointed_file_ID, key, value])
                writer.writerow([file_ID, pointed_file_ID])
            except:
                # print('symlink may point to a non-exist file: ' + str(key) + ' -> ' + str(value))
                skipped_file.write('symlink may point to a non-exist file: ' + str(key) + ' -> ' + str(value) + '\n')

    with open('csv/hardLink_t.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        writer.writerow(hard_link_attr)
        for info in inode_dev_lst:
            writer.writerow(info)

   # helper csv
    os.makedirs(os.path.dirname('helpercsv/fileExtensions.csv'), exist_ok=True)
    os.makedirs(os.path.dirname('helpercsv/fakeFilePath.csv'), exist_ok=True)
    
    with open('helpercsv/fileExtensions.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        writer.writerow(['file_ext', 'cnt'])
        for key, value in cnt_by_extension.items():
            writer.writerow([key, value])
    
    # helper csv
    with open('helpercsv/fakeFilePath.csv', 'w+') as w_csv:
        writer = csv.writer(w_csv)
        writer.writerow(['fake_file_path'])
        for path in regular_file_fake_path:
            writer.writerow([path])

    print('\n---------------------')
    print('total directory count: ' + str(d_file_cnt))
    print('total regular file count: ' + str(r_file_cnt))
    print('total symlink count: ' + str(l_file_cnt))
    print('total character special file count: ' + str(c_file_cnt))
    print('total block special file count: ' + str(b_file_cnt))
    print('total fifo file count: ' + str(p_file_cnt))
    print('total socket count: ' + str(s_file_cnt))
    print('total door count: ' + str(do_file_cnt))
    print('total event port count: ' + str(ep_file_cnt))
    print('total whiteout count: ' + str(wo_file_cnt))
    print('---------------------\n')

    skipped_file.close()
    
if __name__ == '__main__':
    main()