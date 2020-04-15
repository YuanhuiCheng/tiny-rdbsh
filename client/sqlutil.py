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
            read_obj.close()
        os.remove(self.name)

    def cprint(self):
        with open(self.name, 'r') as read_obj:
            print(read_obj.read())
            read_obj.close()
        os.remove(self.name)

class SQLUtil(object):
    def __init__(self):
        self.connection = pymysql.connect(host='localhost',
                             user='zz',
                             password='152314zzz',
                             db='rdbsh2',
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
        return '^' + path.replace('/', '\\/').replace('*', '[^\\/]*') + '$'

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

    @staticmethod
    def cluster_path_regex(path):
        if path == "/":
            return "^" + path.replace('/', '\\/') + ".+$"
        else:
            return "^" + path.replace('/', '\\/') + "\\/.+$"

    def check_path_exists(self, path, ftype):
        with self.connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `abspath` FROM `file_t` WHERE `abspath`='%s' AND `ftype`='%s'" % (path, ftype)
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
            cursor.execute(sql)
            results = cursor.fetchall()
            total_size = 0
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
                    total_size += size
                    date_time = datetime.fromtimestamp(result['mtime'])
                    time_str = date_time.strftime('%B %d %H:%M:%S')
                    slink_name = result['sname']
                    file = File(fid, name, permission, num_links, user, group, size, time_str, slink_name)
                    ls_set.append(file)
        return ls_set, total_size

    # echo all the $PATH with priority
    def get_path_var(self):
        with self.connection.cursor() as cursor:
            sql = "SELECT `abspath` FROM `pathVar_t` p JOIN `file_t` f ON p.fid = f.fid ORDER BY p.prior"
            cursor.execute(sql)
            results = cursor.fetchall()
            path_vars = []
            for result in results:
                path_var = result['abspath'].rstrip('\r')
                path_vars.append(path_var)
            return path_vars
    # add path into the $PATH
    def add_path_var(self, path, last_flag):
        with self.connection.cursor() as cursor:
            # first check if the path exists in the file_t table
            sql = "SELECT `fid` FROM `file_t` WHERE `abspath` = '%s'" % (path)
            cursor.execute(sql)
            results = cursor.fetchall()
            if not results:
                print("Error: %s doesn't exists" % (path))
                return
            fid = results[0]['fid']
            # check if the path already exists in the path variable
            sql = "SELECT EXISTS(SELECT * from `pathVar_t` WHERE `fid` = %d)" % (fid)
            cursor.execute(sql)
            results = cursor.fetchall()
            if results[0] == 1:
                print("Error: %s already exists in the $PATH" % (path))
                return
            # insert the path into the path variable with proper priority
            if last_flag:
                sql = "INSERT INTO `pathVar_t`(prior, fid) SELECT MAX(prior) + 1, %d FROM `pathVar_t`" % (fid)
                cursor.execute(sql)
            else:
                update_prior_sql = "UPDATE `pathVar_t` SET prior = prior + 1"
                insert_sql = "INSERT INTO `pathVar_t`(prior, fid) VALUES (0, %d)" % (fid)
                cursor.execute(update_prior_sql)
                cursor.execute(insert_sql)

            self.connection.commit()
            return

    def delete_path_var(self, path):
        with self.connection.cursor() as cursor:
            # check if path is in the $PATH
            sql = "SELECT prior FROM `pathVar_t` p JOIN `file_t` f ON p.fid = f.fid WHERE `abspath` = '%s'" % (path)
            cursor.execute(sql)
            results = cursor.fetchall()
            if not results:
                print("Error: %s doesn't exist in the $PATH" % (path))
                return
            curr_prior = results[0]['prior']
            delete_sql = "DELETE FROM `pathVar_t` WHERE `fid` = (SELECT `fid` FROM `file_t` WHERE `abspath` = '%s')" % (path)
            update_prior_sql = "UPDATE `pathVar_t` SET prior = prior - 1 WHERE prior > %d" % (curr_prior)
            cursor.execute(delete_sql)
            cursor.execute(update_prior_sql)
            
            self.connection.commit()
            return

    # execute executable file
    def get_executable(self, args):
        name = args[0]
        path_vars = self.get_path_var()
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

    def find(self, path, name=None, user=None, inodeNum=None, linkNum=None):
        find_set = []
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
            if inodeNum:
                sql += " AND `F.inode` = '%s'" % (inodeNum)
            if linkNum:
                sql += " AND `F.numoflinks` = '%s'" % (linkNum)
            cursor.execute(sql)
            print(sql)
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

    def cat(self, abspath):
        with self.connection.cursor() as cursor:
            sql = "SELECT fid, name, ftype FROM file_t WHERE abspath = '%s' AND (ftype = 'd' OR ftype = '-')" % (abspath)
            cursor.execute(sql)
            results = cursor.fetchall()
            if not results:
                print("cat: %s: No such file or directory" % (abspath.split('/')[-1]))
                return
            if results[0]['ftype'] == 'd':
                print("cat: %s: Is a directory" % (abspath.split('/')[-1]))

            filename = results[0]['name']
            fid = results[0]['fid']
            file = File(fid, filename)
            fileContent_sql = "SELECT unhex(data) as data from fileContent_t WHERE fid = %d" % (results[0]['fid'])
            cursor.execute(fileContent_sql)
            results = cursor.fetchall()
            if os.path.exists(filename):
                os.remove(filename)
            f = open(filename, "wb")
            f.write(results[0]['data'])
            f.close()
        return file


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









