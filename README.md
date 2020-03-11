## ECE356-Unix-Dumb-Project

#### How to move UNIX box data into your local mysql?

First, run `cd move_unix_box`

**Move UNIX box data to your local machine hosted mysql**
Run `./build.sh [mysql_user] [mysql_pwd]`

For example, `./build.sh yuanhui 12345ssdlh`

**Move UNIX box data to your local machine hosted mysql and vm hosted mysql**
Run `./build.sh [mysql_user] [mysql_pwd] [remote_url] [remote_sql_user] [remote_sql_pwd]`

For example, `./build.sh root 12345ssdlh 192.168.56.101 yuanhui ssdlh12345`


