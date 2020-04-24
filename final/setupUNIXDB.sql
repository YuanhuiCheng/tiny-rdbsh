set global local_infile = true;

drop database if exists rdbsh;
create database rdbsh;
use rdbsh;

drop table if exists file_t;
drop table if exists user_t;
drop table if exists group_t;
drop table if exists pathVar_t;
drop table if exists symbolicLink_t;
drop table if exists hardLink_t;
drop table if exists fileContent_t;

-- create tables

-- fid: file ID
-- inode: index node that describes the attributes and disk block locations
-- dev: the device that inode resides on
-- ftype: file type (d: Directory, -: Regular, l: Symoblic link, c: Character special, b: Block special, p: FIFO, s: Socket, do: Door, ep: Event port, wo: Whiteout)
-- op: owner permission
-- gp: group permission
-- tp: other permission
-- numoflinks: the number of hard links to a particular inode
-- uid: ID of the owner of the file
-- size: file size, expressed in bytes
-- ctime: creation time of the file
-- name: file name
-- abspath: absolute path
create table file_t (
    fid int,
    inode int,
    dev int,
    ftype varchar(10), 
    op int,
    gp int,
    tp int,
    numoflinks int,
    uid int,
    size int,
    ctime float, 
    mtime float,
    name varchar(255),
    abspath varchar(255)
);

-- uid: user ID
-- name: user name
-- gid: ID of the group that the user belongs to
create table user_t (
    uid int,
    name varchar(255),
    gid int
);

-- gid: group ID
-- name: group name
create table group_t (
    gid int,
    name varchar(255)
);

-- prior: priority of path variable
-- abspath: absolute path of path variable
create table pathVar_t (
    prior int,
    abspath varchar(255)
);

-- abspath: absolute path of the symbolic link
-- pabspath: absolute path of the file the link points to
create table symbolicLink_t (
    abspath varchar(255),
    pabspath varchar(255)
);

-- fid: file id
-- data: the file content
create table fileContent_t (
    fid int,
    data longblob
);

-- add constraints

-- add primary keys

alter table file_t add primary key(abspath);
alter table group_t add primary key(gid);
alter table user_t add primary key(uid);
alter table pathVar_t add primary key(abspath);
alter table symbolicLink_t add primary key(abspath, pabspath);
alter table fileContent_t add primary key(fid);

-- add foreign keys

alter table file_t 
    add foreign key(uid) references user_t(uid);
-- alter table fileContent_t add foreign key(fid) references file_t(fid);
alter table pathVar_t add foreign key(abspath) references file_t(abspath);
alter table symbolicLink_t 
    add foreign key(abspath) references file_t(abspath),
    add foreign key(pabspath) references file_t(abspath);

-- add indexes

-- create index abspath_index on file_t(abspath);
create index filetype_index on file_t(ftype);
create index filename_index on file_t(name);
create index fileid_index on file_t(fid);

-- load csv

load data local infile 'csv/group_t.csv' into table group_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile 'csv/user_t.csv' into table user_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile 'csv/file_t.csv' into table file_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile 'csv/pathVar_t.csv' into table pathVar_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile 'csv/symbolicLink_t.csv' into table symbolicLink_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

-- load dumped file contents into fileContent_t table
source file_contents/rdbsh_fileContent.sql;
