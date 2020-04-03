import pymysql.cursors
import os
from datetime import datetime

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

class SQLUtil(object):
    def __init__(self):
        self.connection = pymysql.connect(host='localhost',
                             user='zz',
                             password='152314zzz',
                             db='rdbsh',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    @staticmethod    
    def build_path_regex(path):
        """ Make path to be in regex format ^\/path\/[^\/]+$"""
        new_path = '^'
        for c in path:
            if c == '/':
                new_path += "\\" + '/'
            else:
                new_path += c

        if path == "/":
            new_path += "[^\\/]+\\r$"
        else:
            new_path += "\\/[^\\/]+\\r$"
        return new_path

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
            sql = "SELECT `abspath` FROM `file_t` WHERE `abspath`='%s\r' AND `ftype`='%s'" % (path, ftype)
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
            WHERE `abspath` REGEXP '%s'" % self.build_path_regex(path)
            # print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()
            # print(results)
            for result in results:
                # Remove trailing \r and get path string after current path
                # temp_path = result['abspath'].rstrip('\r')[len(path):].lstrip('/')
                name = result['name']
                fid = result['fid']
                if not props:
                    ls_set.append(File(fid, name))
                else:
                    permission = self.get_permission(result)
                    num_links = result['numoflinks']
                    user = result['user_t.name'].rstrip('\r')
                    group = result['group_t.name'].rstrip('\r')
                    print(result)
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
            print(sql)
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








