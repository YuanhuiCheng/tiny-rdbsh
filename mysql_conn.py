import mysql.connector

RDBSH_DB='rdbsh'
TABLES=['file', 'fileType', 'permissionType', 'user', 'group', 'pathVar',
    'symbolicLink', 'hardLink']

FILE_TABLE_NAME='file'
FILE_TYPE_TABLE_NAME='fileType'
PERMISSION_TYPE_TABLE_NAME='permissionType'
USER_TABLE_NAME='user'
GROUP_TABLE_NAME='group'
PATH_VAR_TABLE_NAME='pathVar'
SYMLINK_TABLE_NAME='symbolicLink'
HARD_LINK_TABLE_NAME='hardLink'

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
    for table in tables:
        csv_path = os.path.abspath('csv/'+table+'.csv')
        mycursor.execute("""load data local infile {} into table {}
        fields terminated by ','
        lines terminated by '\n'
        ignore 1 lines""".format(csv_path, table))


def main():
    mydb = mysql.connector.connect(user='root', password='cxg651240',
                              host='127.0.0.1',
                              auth_plugin='mysql_native_password')
    mycursor = mydb.cursor()
    mycursor.execute('create database if not exists {}'.format(RDBSH_DB))
    mycursor.execute('use {}'.format(RDBSH_DB))

    create_tables(mycursor)

    mydb.close()

if __name__ == '__main__':
    main()