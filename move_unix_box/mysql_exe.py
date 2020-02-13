import sys
import os
import mysql.connector

RDBSH_DB='rdbsh'
TABLES=['file_t', 'fileType_t', 'permissionType_t', 'user_t', 'group_t', 'pathVar_t',
    'symbolicLink_t', 'hardLink_t']

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

def create_tables(mycursor):
    mycursor.execute("""create table {} (
        id int, 
        inode int,
        dev int, 
        type varchar(10), 
        op int,
        gp int,
        tp int,
        num_of_links int,
        owner_id int,
        group_id int,
        size int,
        time float, 
        name varchar(255),
        parentID int,
        abs_path varchar(255)
    )""".format(FILE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id varchar(10),
        type varchar(20)
    )""".format(FILE_TYPE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id int,
        pr varchar(10),
        pw varchar(10),
        pe varchar(10)
    )""".format(PERMISSION_TYPE_TABLE_NAME))

    mycursor.execute("""create table {} (
        id int,
        name varchar(255),
        path varchar(255),
        groupId int
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
    mycursor.execute('create database if not exists {}'.format(RDBSH_DB))
    mycursor.execute('use {}'.format(RDBSH_DB))

    drop_tables(mycursor)
    create_tables(mycursor)
    load_csv(mycursor)

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