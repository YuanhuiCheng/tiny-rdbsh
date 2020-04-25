import pymysql.cursors
import os
import re
from datetime import datetime
from tabulate import tabulate
import sys

DB_HOST = 'localhost'
DB_USER = 'zz'
DB_PASSWORD = '152314zzz'
DB_NAME = 'rdbsh'
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
        self.connection = pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASSWORD,
                             db=DB_NAME,
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
        permission_default_l = 'lrwxrwxrw'
        permission_bin = ''
        permission = ''
        if result['ftype'] == 'd':
            permission_bin += '1'
        elif result['ftype'] == 'l':
            permission_bin += '1'
            permission_default = permission_default_l
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
            (select symbolicLink_t.abspath AS fpath, symbolicLink_t.pabspath AS ppath, symbolic.name AS sname from symbolicLink_t INNER JOIN (SELECT abspath, name from file_t) AS symbolic ON symbolic.abspath=symbolicLink_t.pabspath) S \
            ON file_t.abspath=S.fpath \
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
            sql = "SELECT p.abspath AS 'path' FROM `pathVar_t` p JOIN `file_t` f USING (abspath) ORDER BY p.prior"
            cursor.execute(sql)
            results = cursor.fetchall()
            path_vars = []
            for result in results:
                path_var = result['path'].rstrip('\r')
                path_vars.append(path_var)
            return path_vars
    # add path into the $PATH
    def add_path_var(self, path, last_flag):
        with self.connection.cursor() as cursor:
            # first check if the path exists in the file_t table
            sql = "SELECT `fid` FROM `file_t` WHERE `abspath` = '%s'" % (path)
            cursor.execute(sql)
            result = cursor.fetchone()
            if not result:
                print("Error: %s doesn't exists" % (path))
                return
            # check if the path already exists in the path variable
            sql = "SELECT EXISTS(SELECT * from `pathVar_t` WHERE `abspath` = '%s') AS exist" % (path)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result['exist'] == 1:
                print("Error: %s already exists in the $PATH" % (path))
                return
            # insert the path into the path variable with proper priority
            if last_flag:
                sql = "INSERT INTO `pathVar_t`(prior, abspath) SELECT MAX(prior) + 1, '%s' FROM `pathVar_t`" % (path)
                cursor.execute(sql)
            else:
                update_prior_sql = "UPDATE `pathVar_t` SET prior = prior + 1"
                insert_sql = "INSERT INTO `pathVar_t`(prior, abspath) VALUES (0, '%s')" % (path)
                cursor.execute(update_prior_sql)
                cursor.execute(insert_sql)

            self.connection.commit()
            return

    def delete_path_var(self, path):
        with self.connection.cursor() as cursor:
            # check if path is in the $PATH
            sql = "SELECT prior FROM `pathVar_t` WHERE `abspath` = '%s'" % (path)
            cursor.execute(sql)
            result = cursor.fetchone()
            if not result:
                print("Error: %s doesn't exist in the $PATH" % (path))
                return
            curr_prior = result['prior']
            delete_sql = "DELETE FROM `pathVar_t` WHERE `abspath` = '%s'" % (path)
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
            exefiles, _ = self.ls(path_var)
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
            result = cursor.fetchone()
            if os.path.exists("tempexec"):
                os.remove("tempexec")
            f = open("tempexec", "wb")
            f.write(result['data'])
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
            (select symbolicLink_t.abspath AS fpath, symbolicLink_t.pabspath AS ppath, symbolic.name AS sname from symbolicLink_t INNER JOIN (SELECT abspath, name from file_t) AS symbolic ON symbolic.abspath=symbolicLink_t.pabspath) S \
            ON F.abspath=S.fpath \
            WHERE `abspath` like '%s'" % (abspath)
            if name:
                name = name.replace("*", "%").replace("?", "_")
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

    def cat_create(self, name, abspath, content):
        with self.connection.cursor() as cursor:
            get_fid_inode = "SELECT max(fid) AS fidMax, max(inode) AS inodeMax FROM file_t"
            cursor.execute(get_fid_inode)
            result = cursor.fetchone()
            fid = result['fidMax'] + 1
            inode = result['inodeMax'] + 1
            current_time = datetime.now().timestamp()
            size = sys.getsizeof(content)
            insert_filet_sql = "INSERT INTO file_t VALUES (%d, %d, %d, '%s', %d, %d, %d, %d, %d, %d, %f, %f, '%s', '%s')" % \
                (int(fid), int(inode), 112, '-', 6, 4, 4, 1, 0, size, current_time, current_time, name, abspath)
            cursor.execute(insert_filet_sql)
            insert_fileContent_sql = "INSERT INTO fileContent_t VALUES (%d, hex('%s'))" % (int(fid), content)
            cursor.execute(insert_fileContent_sql)
            #self.connection.commit()
        return


    def cat_view(self, abspath):
        with self.connection.cursor() as cursor:
            sql = "SELECT fid, name, ftype FROM file_t WHERE abspath = '%s' AND (ftype = 'd' OR ftype = '-' OR ftype = 'l')" % (abspath)
            cursor.execute(sql)
            result = cursor.fetchone()
            if not result:
                print("cat: %s: No such file or directory" % (abspath.split('/')[-1]))
                return
            if result['ftype'] == 'd':
                print("cat: %s: Is a directory" % (abspath.split('/')[-1]))
                return
            filename = result['name']
            if result['ftype'] == 'l':
                fid = result['fid']
                ln_sql = "SELECT F.fid AS fid, name FROM file_t F INNER JOIN symbolicLink_t S ON F.abspath = S.pabspath WHERE S.abspath = '%s'" % (abspath)
                print(ln_sql)
                cursor.execute(ln_sql)
                result = cursor.fetchone()
                if not result:
                    print("cat: %s: No such file or directory" % (abspath.split('/')[-1]))
                    return
            fid = result['fid']
            file = File(fid, filename)
            fileContent_sql = "SELECT unhex(data) as data from fileContent_t WHERE fid = %d" % (fid)
            cursor.execute(fileContent_sql)
            result = cursor.fetchone()
            if os.path.exists(filename):
                os.remove(filename)
            f = open(filename, "wb")
            f.write(result['data'])
            f.close()
        return file

    def slink(self, oriFile, newFile):
        with self.connection.cursor() as cursor:
            fetchori_sql = "SELECT abspath, dev FROM file_t WHERE abspath = '%s' AND ftype = '-'" % (oriFile)
            cursor.execute(fetchori_sql)
            result = cursor.fetchone()
            if not result:
                print("%s: No such file" % (oriFile.split('/')[-1]))
                return
            pabspath = result['abspath']
            dev = result['dev']
            # Get largest fid and inode
            get_fid_inode = "SELECT max(fid) AS fidMax, max(inode) AS inodeMax FROM file_t"
            cursor.execute(get_fid_inode)
            result = cursor.fetchone()
            fid = result['fidMax'] + 1
            inode = result['inodeMax'] + 1
            current_time = datetime.now().timestamp()
            # pid 去掉 + dev
            insert_filet_sql = "INSERT INTO file_t VALUES (%d, %d, %d, '%s', %d, %d, %d, %d, %d, %d, %f, %f, '%s', '%s')" % \
                (int(fid), int(inode), int(dev), 'l', 7, 5, 5, 1, 0, 9, current_time, current_time, newFile.split('/')[-1], newFile)
            insert_slinkt_sql = "INSERT INTO symbolicLink_t VALUES ('%s', '%s')" % (newFile, pabspath)
            cursor.execute(insert_filet_sql)
            cursor.execute(insert_slinkt_sql)
            #self.connection.commit()
        return

    def hlink(self, oriFile, newFile):
        with self.connection.cursor() as cursor:
            fetchori_sql = "SELECT * FROM file_t WHERE abspath = '%s' AND ftype = '-'" % (oriFile)
            cursor.execute(fetchori_sql)
            result = cursor.fetchone()
            if not result:
                print("%s: No such file" % (oriFile.split('/')[-1]))
                return
            numoflinks = result['numoflinks'] + 1
            current_time = datetime.now().timestamp()
            insert_filet_sql = "INSERT INTO file_t VALUES (%d, %d, %d, '%s', %d, %d, %d, %d, %d, %d, %f, %f, '%s', '%s')" % \
                (result['fid'], result['inode'], result['dev'], result['ftype'], result['op'], result['gp'], result['tp'], numoflinks, 0, result['size'], current_time, current_time, newFile.split('/')[-1], newFile)
            update_filet_sql = "UPDATE `file_t` SET numoflinks = %d WHERE abspath = '%s'" % (numoflinks, oriFile)
            cursor.execute(insert_filet_sql)
            cursor.execute(update_filet_sql)
            #self.connection.commit()
        return


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

    def quit(self):
        self.connection.close()
        return









