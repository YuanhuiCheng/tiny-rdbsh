import pymysql.cursors
import os
from datetime import datetime

class File(object):
    def __init__(self, fid, name, permission=None, num_links=None, user=None, group=None, size=None, mtime=None, slink_name=None):
        self.fid = fid
        self.name = name
        self.permission = permission
        self.num_links = num_links
        self.user = user
        self.group = group
        self.size = size
        self.mtime = mtime
        self.slink_name = slink_name

    def lprint(self):
        if self.slink_name is None:
            name = self.name
        else:
            name = "%s -> %s" % (self.name, self.slink_name)
        print(self.permission, self.num_links, self.user, self.group, self.size, self.mtime, name)
class SQLUtil(object):
    def __init__(self):
        self.connection = pymysql.connect(host='localhost',
                             user='zz',
                             password='152314zzz',
                             db='rdbsh',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

        self.file_conn = pymysql.connect(host='localhost',
                             user='zz',
                             password='152314zzz',
                             db='rdbshfile',
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
            print(path)
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

    def path_var(self):
        with self.connection.cursor() as cursor:
            sql = "SELECT `abspath` FROM `pathVar_t` p JOIN `file_t` f ON p.fid = f.fid"
            cursor.execute(sql)
            results = cursor.fetchall()
            path_vars = []
            for result in results:
                path_var = result['abspath'].rstrip('\r')
                path_vars.append(path_var)
            print(':'.join(path_vars))
            return path_vars

    def get_executable(self, name):
        path_vars = self.path_var()
        for path_var in path_vars:
            found = False
            fid_name_tups = self.ls(path_var)
            for fid_name_tup in fid_name_tups:
                if fid_name_tup[1] == name:
                    print(fid_name_tup)
                    found = True
                    break
            if found:
                break
        with self.file_conn.cursor() as cursor:
            table_name = str(fid_name_tup[0]) + "_"
            #sql = "SELECT * FROM %s ORDER BY `ln`" % table_name
            sql = "SELECT * FROM testBlob ORDER BY `ln`"
            cursor.execute(sql)
            results = cursor.fetchall()
            if os.path.exists("tempexec2"):
                os.remove("tempexec2")

            f = open("tempexec2", "ab")
            for result in results:
                f.write(result['data'])
            f.close()





