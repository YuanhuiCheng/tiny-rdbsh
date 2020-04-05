import pymysql.cursors
import os
import re
from datetime import datetime
from tabulate import tabulate

# create a file object for pretty print
class File(object):
    def __init__(self, fid, name, permission=None, num_links=None, user=None, group=None, size=None, mtime=None, slink_name=None, abs_path=None):
        self.fid = fid
        self.name = name
        self.permission = permission
        self.num_links = num_links
        self.user = user
        self.group = group
        self.size = size
        self.mtime = mtime
        self.slink_name = slink_name
        self.abs_path = abs_path

    # ls -l pretty print
    def lprint(self):
        if self.slink_name is None:
            name = self.name
        else:
            name = "%s -> %s" % (self.name, self.slink_name)
        print(self.permission, self.num_links, self.user, self.group, self.size, self.mtime, name)

    # find pretty print
    def fprint(self, work_dir):
        # convert absolute path to relative path
        path = os.path.relpath(self.abs_path, work_dir) 
        if self.slink_name:
            path = "%s -> %s" % (path, self.slink_name)
        print(self.permission, self.num_links, self.user, self.group, self.size, self.mtime, path)

    # grep pretty print
    def gprint(self, pattern):
        print(pattern)
        with open(self.name, 'r') as read_obj:
            # Read all lines in the file one by one
            line_num = 1
            for line in read_obj:
                # For each line, check if line contains the string
                # print(re.search(pattern, line))
                if re.search(pattern, line):
                    # add in results
                    print("%s: %d %s" % (self.name, line_num, line))
                
                line_num = line_num + 1

        os.remove(self.name)

class SQLUtil(object):
    def __init__(self):
        self.connection = pymysql.connect(host='localhost',
                             user='root',
                             password='wdtda2907',
                             db='rdbsh',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    @staticmethod    
    def ls_path_regex(path):
        """ Make path to be in regex format ^\/path\/[^\/]+$"""
        if path == "/":
            return "^" + path.replace('/', '\\/') + "[^\\/]+$"
        else:
            return "^" + path.replace('/', '\\/') + "\\/[^\\/]+$"

    @staticmethod
    def grep_path_regex(path):
        return '^' + path.replace('/', '\\/').replace('*', '[^\\/]*')

    @staticmethod
    def cluster_path_regex(path):
        if path == "/":
            return "^" + path.replace('/', '\\/') + ".+$"
        else:
            return "^" + path.replace('/', '\\/') + "\\/.+$"

    @staticmethod
    def get_permission(result):
        permission_default = 'drwxrwxrw'
        permission_bin = ''
        permission = ''
        if result['ftype'] == 'd':
            permission_bin += '1'
        else:
            permission_bin += '0'
        permission_bin += "{0:b}".format(result['op']).zfill(3)
        permission_bin += "{0:b}".format(result['gp']).zfill(3)
        permission_bin += "{0:b}".format(result['tp']).zfill(3)
        for i in range(len(permission_default)):
            if permission_bin[i] == '0':
                permission += '-'
            else:
                permission += permission_default[i]
        return permission

    def check_path_exists(self, path, ftype):
        with self.connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `abspath` FROM `file_t` WHERE `abspath`='%s' AND `ftype`='%s'" % (path, ftype)
            # print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()
            if len(results) == 0:
                return False
            else:
                return True

    def ls(self, path, props=False):
        ls_set = []
        with self.connection.cursor() as cursor:
            # Read a single record
            # print(path)
            sql = "\
            SELECT * FROM file_t \
            INNER JOIN user_t \
            USING (uid) \
            INNER JOIN group_t \
            USING (gid) \
            LEFT JOIN \
            (select symbolicLink_t.fid AS fid, symbolicLink_t.pfid AS sid, symbolic.name AS sname from symbolicLink_t INNER JOIN (SELECT fid, name from file_t) AS symbolic ON symbolic.fid=symbolicLink_t.pfid) S \
            ON file_t.fid=S.fid \
            WHERE `abspath` REGEXP '%s'" % self.ls_path_regex(path)
            print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()
            for result in results:
                name = result['name']
                fid = result['fid']
                if not props:
                    ls_set.append(File(fid, name))
                else:
                    permission = self.get_permission(result)
                    num_links = result['numoflinks']
                    user = result['user_t.name'].rstrip('\r')
                    group = result['group_t.name'].rstrip('\r')
                    size = result['size']
                    date_time = datetime.fromtimestamp(result['mtime'])
                    time_str = date_time.strftime('%B %d %H:%M:%S')
                    slink_name = result['sname']
                    file = File(fid, name, permission, num_links, user, group, size, time_str, slink_name)
                    ls_set.append(file)
        return ls_set

    # echo all the path variable
    def path_var(self):
        with self.connection.cursor() as cursor:
            sql = "SELECT `abspath` FROM `pathVar_t` p JOIN `file_t` f ON p.fid = f.fid"
            cursor.execute(sql)
            results = cursor.fetchall()
            path_vars = []
            for result in results:
                path_var = result['abspath'].rstrip('\r')
                path_vars.append(path_var)
            return path_vars

    # execute executable file
    def get_executable(self, args):
        name = args[0]
        path_vars = self.path_var()
        for path_var in path_vars:
            found = False
            exefiles = self.ls(path_var)
            for exefile in exefiles:
                if exefile.name == name:
                    found = True
                    break
            if found:
                break
        if not found:
            # cannot find the command
            print("-bash: %s: command not found" % (name))
            return
        with self.connection.cursor() as cursor:
            sql = "SELECT unhex(data) AS data FROM fileContent_t where fid = %s" % (exefile.fid)
            cursor.execute(sql)
            results = cursor.fetchall()
            if os.path.exists("tempexec"):
                os.remove("tempexec")
            f = open("tempexec", "wb")
            f.write(results[0]['data'])
            f.close()
        arguments = " ".join(args[1:])
        os.system("./tempexec " + arguments)

    def find(self, path, args):
        find_set = []
        name = user = inodeNum = linkNum = None
        for i in range(len(args)):
            if args[i] == '-name':
                i = i + 1
                name = args[i]
            elif args[i] == '-user':
                i = i + 1
                user = args[i]
            # elif args[i] == '-perm':
            #     i = i + 1
            #     perm = args[i]
            elif args[i] == '-inum':
                i = i + 1
                inodeNum = args[i]
            elif args[i] == '-links':
                i = i + 1
                linkNum = args[i]
        with self.connection.cursor() as cursor:
            # find path
            abspath = path + "%"
            sql = "\
            SELECT * FROM file_t F\
            INNER JOIN user_t U \
            USING (uid) \
            INNER JOIN group_t G\
            USING (gid) \
            LEFT JOIN \
            (select symbolicLink_t.fid AS fid, symbolicLink_t.pfid AS sid, symbolic.name AS sname from symbolicLink_t INNER JOIN (SELECT fid, name from file_t) AS symbolic ON symbolic.fid=symbolicLink_t.pfid) S \
            ON F.fid=S.fid \
            WHERE `abspath` like '%s'" % (abspath)
            if name:
                name = name.replace("*", "%")
                sql += " AND F.name like '%s'" % (name)
            if user:
                if user.isdigit():
                    sql += " AND (F.uid = %d)" % int(user)
                else:
                    sql += " AND (U.name = '%s')" % (user)
            # if perm:
            #     sql += " AND "
            if inodeNum:
                sql += " AND `F.inode` = '%s'" % (inodeNum)
            if linkNum:
                sql += " AND `F.numoflinks` = '%s'" % (linkNum)
            cursor.execute(sql)
            results = cursor.fetchall()
            for result in results:
                name = result['name']
                fid = result['fid']
                permission = self.get_permission(result)
                num_links = result['numoflinks']
                user = result['U.name'].rstrip('\r')
                group = result['G.name'].rstrip('\r')
                size = result['size']
                date_time = datetime.fromtimestamp(result['mtime'])
                time_str = date_time.strftime('%B %d %H:%M:%S')
                slink_name = result['sname']
                abs_path = result['abspath'].rstrip('\r')
                file = File(fid, name, permission, num_links, user, group, size, time_str, slink_name, abs_path)
                find_set.append(file)
        return find_set

    def grep(self, pattern, abspath):
        file_set = []
        with self.connection.cursor() as cursor:
            sql = "SELECT fid, unhex(data) as data, name FROM file_t \
            INNER JOIN fileContent_t USING (fid) \
            WHERE `abspath` REGEXP '%s' AND `ftype` = '-' AND unhex(data) REGEXP '%s'" % (self.grep_path_regex(abspath), pattern)
            print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()

            for result in results:
                filename = result['name'].rstrip('\r')
                file = File(result['fid'], filename)
                file_set.append(file)
                if os.path.exists(filename):
                    os.remove(filename)
                f = open(filename, "wb")
                f.write(result['data'])
                f.close()

        return file_set

    def extcluster(self, abspath):
        with self.connection.cursor() as cursor:
            sql = "SELECT fid, name, size FROM file_t WHERE ftype = '-' AND abspath REGEXP '%s'" \
                % self.cluster_path_regex(abspath)
            cursor.execute(sql)
            results = cursor.fetchall()
            ftype_dict = {}
            for result in results:
                pattern = '^.+\\.[^\\.0-9]+$'
                # splits = result['name'].split('.')
                if re.search(pattern, result['name']) is None:
                    if 'N/A' in ftype_dict:
                        ftype_dict['N/A'].append(result['size'])
                    else:
                        ftype_dict['N/A'] = [result['size']]
                else:
                    ext = result['name'].split('.')[-1]
                    if ext in ftype_dict:
                        ftype_dict[ext].append(result['size'])
                    else:
                        ftype_dict[ext] = [result['size']]

            sorted_ftype = {k: v for k, v in sorted(ftype_dict.items(), key=lambda item: -len(item[1]))}
            sorted_tab_list = [[k, len(v), str(round(sum(v) / len(v)))] for k, v in sorted_ftype.items()]
            print(tabulate(sorted_tab_list, headers=['Ext', 'Count', 'Avg Size']))










