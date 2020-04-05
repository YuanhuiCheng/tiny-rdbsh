import sys
import os
import csv
import mysql.connector
import string
from pathlib import Path
import mimetypes

RDBSH_DB='rdbsh'
RDBSH_FILE='rdbshfile'

TABLES=['file_t', 'user_t', 'group_t', 'pathVar_t', 'symbolicLink_t', 'hardLink_t']

FILE_T_ATTR = ['fid', 'inode', 'ftype', 'op', 'gp', 'tp', 'numoflinks', 
    'uid', 'size', 'ctime', 'mtime', 'name', 'pid', 'abspath']

FILE_TABLE_NAME='file_t'
USER_TABLE_NAME='user_t'
GROUP_TABLE_NAME='group_t'
PATH_VAR_TABLE_NAME='pathVar_t'
SYMLINK_TABLE_NAME='symbolicLink_t'
HARD_LINK_TABLE_NAME='hardLink_t'
FILE_CONTENT_TABLE_NAME='fileContent_t'

def drop_tables(mycursor): 
    for table in TABLES:
        mycursor.execute('drop table if exists {}'.format(table))

def load_reg_file_content(mycursor):
    file_id_by_path = {}

    with open('csv/file_t.csv') as file_t:
        reader = csv.reader(file_t)
        next(reader)

        for row in reader:
            try:
                abs_path = row[FILE_T_ATTR.index('abspath')]
                file_id = row[FILE_T_ATTR.index('fid')]
                file_id_by_path[abs_path] = file_id
            except:
                print('error happens: ' + str(row))

    error_info_file = 'err/error_info.txt'
    os.makedirs(os.path.dirname(error_info_file), exist_ok=True)

    with open('helpercsv/fakeFilePath.csv') as r_file, open(error_info_file, 'w') as err_file:
        reader = csv.reader(r_file)
        next(reader)

        temp_unix_len = len('temp_unix')

        mycursor.execute("""
            create table {} (
            fid int,
            data longblob)
            """.format(FILE_CONTENT_TABLE_NAME))

        for path in reader:
            fake_file_path = os.path.abspath(path[0])
            
            temp_unix_index = fake_file_path.index('temp_unix')
            start_pos = temp_unix_index + temp_unix_len
            real_path = fake_file_path[start_pos:]

            fid = -1
            if real_path in file_id_by_path:
                fid = file_id_by_path[real_path]
            else:
                print('Warn: no ' + str(real_path) + ' found in file_t file')
                continue
            
            with open(fake_file_path, 'rb') as f:
                file_content = f.read()
                try:
                    query = """
                        insert into {} ({}, {})
                        values (%s, hex(%s));
                        """.format(FILE_CONTENT_TABLE_NAME, 'fid', 'data')
                    args = (fid, file_content)
                    mycursor.execute(query, args)
                except mysql.connector.Error as err:
                    print("Error: " + err.msg)
                    print("Failed file path is: " + str(path[0]))

def main():
    sql_user_name = sys.argv[1]
    sql_pwd = sys.argv[2]
    mydb = mysql.connector.connect(user=sql_user_name, password=sql_pwd,
                            host='127.0.0.1',
                            auth_plugin='mysql_native_password',
                            allow_local_infile=True)

    mycursor = mydb.cursor()
    mycursor.execute('set global local_infile = true')

    mycursor.execute('use {}'.format(RDBSH_DB))

    load_reg_file_content(mycursor)

    mydb.commit()
    mydb.close()

    print('\nDone moving UNIX box data to your local machine!')
    
if __name__ == '__main__':
    main()
