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

-- drop table if exists fileContent_t;

-- create tables

-- fid: file ID
-- inode: index node that describes the attributes and disk block locations
-- ftype: file type (d: Directory, -: Regular, l: Symoblic link, c: Character special, b: Block special, p: FIFO, s: Socket, do: Door, ep: Event port, wo: Whiteout)
-- op: owner permission
-- gp: group permission
-- tp: other permission
-- numoflinks: the number of hard links to a particular inode
-- uid: ID of the owner of the file
-- size: file size, expressed in bytes
-- ctime: creation time of the file
-- mtime: modification time of the file
-- name: file name
-- pid: ID of parent directory
-- abspath: absolute path
create table file_t (
    fid int,
    inode int,
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
    pid int,
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

-- fid: ID of the path variables
create table pathVar_t (
    fid int
);

-- fid: ID of the symbolic link
-- pfid: ID of the file the link points to
create table symbolicLink_t (
    fid int,
    pfid int
);

-- inode: index node
-- dev: device that the inode resides
create table hardLink_t (
    inode int,
    dev int
);

-- add constraints

-- add primary keys

alter table hardLink_t add primary key(inode, dev);
alter table file_t add primary key(fid);
alter table group_t add primary key(gid);
alter table user_t add primary key(uid);
alter table symbolicLink_t add primary key(fid, pfid);

-- add foreign keys

alter table file_t add foreign key(inode) references hardLink_t(inode);
alter table file_t 
    add foreign key(uid) references user_t(uid);
alter table pathVar_t add foreign key(fid) references file_t(fid);
alter table symbolicLink_t 
    add foreign key(fid) references file_t(fid),
    add foreign key(pfid) references file_t(fid);

-- add indexes

create index abspath_index on file_t(abspath);

-- load csv

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/hardLink_t.csv' into table hardLink_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/group_t.csv' into table group_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/user_t.csv' into table user_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/file_t.csv' into table file_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/pathVar_t.csv' into table pathVar_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

load data local infile '/Users/yuanhuicheng/Documents/ECE/ECE356/Project/ECE356-Dumb-Project/final/csv/symbolicLink_t.csv' into table symbolicLink_t
    fields terminated by ','
    lines terminated by '\r\n'
    ignore 1 lines;

source rdbsh.sql;
