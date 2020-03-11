import sys
import os
import csv
import mysql.connector
import string
from pathlib import Path

RDBSH_DB='rdbsh'
TABLES=['file_t', 'fileType_t', 'permissionType_t', 'user_t', 'group_t', 'pathVar_t',
    'symbolicLink_t', 'hardLink_t']

FILE_T_ATTR=['id', 'inode', 'dev', 'type', 'op', 'gp', 'tp', 'num_of_links', 
    'owner_id', 'group_id', 'size', 'time', 'name', 'parentID', 'abs_path']

FILE_TABLE_NAME='file_t'
FILE_TYPE_TABLE_NAME='fileType_t'
PERMISSION_TYPE_TABLE_NAME='permissionType_t'
USER_TABLE_NAME='user_t'
GROUP_TABLE_NAME='group_t'
PATH_VAR_TABLE_NAME='pathVar_t'
SYMLINK_TABLE_NAME='symbolicLink_t'
HARD_LINK_TABLE_NAME='hardLink_t'

def drop_tables(mycursor): 
    for table in TABLES:
        mycursor.execute('drop table if exists {}'.format(table))

def load_reg_file_content(mycursor):
    file_id_by_path = {}

    with open('csv/file_t.csv') as file_t:
        reader = csv.reader(file_t)
        next(reader)

        # for row in reader:
        #     abs_path = row[FILE_T_ATTR.index('abs_path')]
        #     file_id = row[FILE_T_ATTR.index('id')]
        #     file_id_by_path[abs_path] = file_id

        for row in reader:
            try:
                abs_path = row[FILE_T_ATTR.index('abs_path')]
                file_id = row[FILE_T_ATTR.index('id')]
                file_id_by_path[abs_path] = file_id
            except:
                print('error happens: ' + str(row))

    error_info_file = 'err/error_info.txt'
    os.makedirs(os.path.dirname(error_info_file), exist_ok=True)

    with open('csv/fakeFilePath.csv') as r_file, open(error_info_file, 'w') as err_file:
        reader = csv.reader(r_file)
        next(reader)

        # table_name_dic = {}

        # remove 'temp_unix' from fake_file_path
        temp_unix_len = len('temp_unix')

        for path in reader:
            fake_file_path = os.path.abspath(path[0])
            table_name = Path(path[0]).resolve().stem
            
            temp_unix_index = fake_file_path.index('temp_unix')
            start_pos = temp_unix_index + temp_unix_len
            # table_name = fake_file_path[temp_unix_len:]
            real_path = fake_file_path[start_pos:]

            if real_path in file_id_by_path:
                # table_name = str(file_id_by_path[real_path])
                table_name = table_name.translate(str.maketrans('', '', string.punctuation))
                table_name = str(file_id_by_path[real_path]) + '_' + table_name
                # table_name = table_name.replace('.', '').replace('-', '')
            else:
                print('Warn: no ' + str(fake_file_path) + ' found in file_t file')

            # print('table name: ' + str(table_name))
            # if table_name in table_name_dic:
            #     print('table name duplicated: ' + table_name)
            #     table_name_dic[table_name] += 1
            #     table_name = table_name + str(table_name_dic[table_name])
            # else:
            #     table_name_dic[table_name] = 0

            try:
                mycursor.execute("""
                create table {} (
                ln int not null auto_increment primary key,
                r text not null)
                """.format(table_name))

                # mycursor.execute("""
                # create table {} (
                # ln int not null auto_increment primary key,
                # r varchar(2048))
                # """.format(table_name))

                mycursor.execute("""
                load data local infile '{}' into table {}
                fields terminated by ''
                lines terminated by '\n' (r)
                """.format(fake_file_path, table_name))

            except mysql.connector.Error as err:
                # print("Error: " + err.msg)
                # print("Failed file path is: " + str(path[0]))
                err_file.write('Error: ' + err.msg + '\n')
                err_file.write('Failed file path is: ' + str(path[0]) + '\n\n')


def create_tables(mycursor):
    mycursor.execute("""create table {} (
        id int, 
        inode int,
        dev int, 
        type varchar(10), 
        op int,
        gp int,
        tp int,
        numOfLinks int,
        ownerID int,
        groupID int,
        size int,
        time float, 
        name varchar(255),
        parentID int,
        absPath varchar(255)
    )""".format(FILE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id varchar(10),
        type varchar(20)
    )""".format(FILE_TYPE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id int primary key,
        pr varchar(10),
        pw varchar(10),
        pe varchar(10)
    )""".format(PERMISSION_TYPE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id int,
        name varchar(255),
        path varchar(255),
        groupID int
    )""".format(USER_TABLE_NAME))

    mycursor.execute("""create table {} (
        id int,
        name varchar(255)
    )""".format(GROUP_TABLE_NAME))

    mycursor.execute("""create table {} (
        var varchar(255),
        path varchar(255),
        fileID int
    )""".format(PATH_VAR_TABLE_NAME))

    mycursor.execute("""create table {} (
        fID int,
        pfID int,
        filePath varchar(255),
        pointedFilePath varchar(255)
    )""".format(SYMLINK_TABLE_NAME))

    mycursor.execute("""create table {} (
        inode int,
        dev int
    )""".format(HARD_LINK_TABLE_NAME))

def load_csv(mycursor):
    for table in TABLES:
        csv_path = os.path.abspath('csv/'+table+'.csv')
        # print('csv path: ' + str(csv_path))
        mycursor.execute("""
        load data local infile '{}' into table {}
        fields terminated by ','
        lines terminated by '\n'
        ignore 1 lines
        """.format(csv_path, table))
        print('load csv into table ' + str(table) + ' done')

def main():
    sql_user_name = sys.argv[1]
    sql_pwd = sys.argv[2]
    mydb = mysql.connector.connect(user=sql_user_name, password=sql_pwd,
                            host='127.0.0.1',
                            auth_plugin='mysql_native_password',
                            allow_local_infile=True)
    # else:
    #     sql_host = sys.argv[1]
    #     sql_user_name = sys.argv[2]
    #     sql_pwd = sys.argv[3]

    #     mydb = mysql.connector.connect(user=sql_user_name, password=sql_pwd,
    #                           host=sql_host,
    #                           auth_plugin='mysql_native_password',
    #                           allow_local_infile=True)

    mycursor = mydb.cursor()
    mycursor.execute('set global local_infile = true')
    mycursor.execute('drop database if exists {}'.format(RDBSH_DB))
    mycursor.execute('create database if not exists {}'.format(RDBSH_DB))
    mycursor.execute('use {}'.format(RDBSH_DB))

    drop_tables(mycursor)
    create_tables(mycursor)
    load_csv(mycursor)
    load_reg_file_content(mycursor)

    mydb.commit()
    mydb.close()

    print('\nDone moving UNIX box data to your local machine!')

    if len(sys.argv) == 6:
        remote_sql_host = sys.argv[3]
        remote_user_name = sys.argv[4]
        remote_user_pwd = sys.argv[5]
        remote_db = mysql.connector.connect(user=remote_user_name, password=remote_user_pwd,
                              host=remote_sql_host,
                              auth_plugin='mysql_native_password')
        remote_cursor = remote_db.cursor()
        remote_cursor.execute('create database if not exists {}'.format(RDBSH_DB))

        remote_db.commit()
        remote_db.close()

        print('\nDone moving UNIX box data to your remote machine!')
    
if __name__ == '__main__':
    main()
