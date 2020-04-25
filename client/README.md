# tiny-rdbsh
ECE 356 Project \(Un*x file system\) 
by Zheng Zhang\(z595zhan\), Yuanhui Cheng\(y82cheng\)


### Introduction
Tiny-rdbsh is a prototype of the Unix-like filesystem on top of an mySQL database. With the provided command line interface, users are able to change and keep track of their working directory, managing a PATH variable then execute executable program that is in the PATH. Moreover, searching and listing the files/directories will be possible as well as showing and extracting the file conetents. Also, both hard link and symbolic links can be managed, and finally, analytics about the average file size for different file type can be retrieved.

### Setups
1. With mySQL Ver 8.0.19 on Linux, `source setupUNIXDB.sql` to setup the database called rdbsh. It may take minutes as loading file contents is time consuming.
2. Update the database connection settings at the beginning of `sqlutil.py` (line 7) with the correct database configurations(DB_HOST, DB_USER and DB_PASSWORD).
3. Since the client side code is written in python3, please make sure python3 is available on you machine. Also, install the necessary libraries with `pip3 install -r requirements.txt`.

### How to start
After make sure all the Setups are correct and python3 path is defined in the environment, run `python3 rdbsh.py`

### Commands Manual
1. cd \[directory\] <br/>
cd command is used to change the current directory. The items in square brackets are optional. When used without specifying any directory name, cd returns the root directory. Both absolute path and local path name are supported, with also `..` represents one level up and `~` or `/` represents the root directory.
2. ls \[-l\] \[directory\] <br/>
ls command is used to list the contents of a directory given to it. It writes results ot standard output. The items in square brackets are optional. When used without specifying option `-l`, ls returns the results with alphabetical order include the hidden file. To show a long listing with detailed information on the directory listing, pass in the `-l` option. Also, directory is optional. Without pass in the directory, it will gives the contents for current working directory.
3. $PATH <br/>
$PATH command is used to list all the PATH variables with priority, separated by `:`.
4. PATH=\[directory\]:$PATH or PATH=$PATH:\[directory\] <br/>
PATH= is used to add a new PATH variable before or after all current PATH variables. `PATH=[directory]:$PATH` is for add new directory as the first to consider Path variable. `PATH=$PATH:[directory]` is for add new directory as the last to consider Path variable. Exceptions handle the case such as not a directory or path already exists in the Path variable.
5. rPath \[directory\] <br/>
rPath command is used to remove the given PATH variable. Exception handles the case such as PATH variable doesn's exist in the PATH variables.
6. \[exec\] \[args\] <br/>
This command is to execute the executable functions under the PATH variables. For example, since `echo` is an executable function under `/bin`, by passing `echo "Welcome to Tiny RDBSH" | sed 's/\(\b[A-Z]\)/\(\1\)/g'`, `/bin/echo` will get executed and gives the output of (W)elcome to (T)iny (R)DBSH.
7. find \[directory\] \[-options\] \[pattern\] <br/>
find command is used to walk a file hierarchy and search files and directories by name, owner, inode number and number of hard links. Directory specifies where to start searching from. Options include the searching criteria. Supported options include `-name`, `-user`, `-inum`, `-links`. Wildcards are supported in the pattern, where `*` matches any string of zero or more characters and `?` matches any single character. The returned results will be shown in a long listing format.
8. grep \[pattern\] \[file\] <br/>
grep command is used to searches a file for a particualr pattern of characters, and displays all lines that contain that pattern. The pattern that is searched in the file is referred to as the regular expression. file accepts wildcards (\* and \/) in the file name.
9. cat \[file\/directory\/link\] <br/>
cat command is used to display contents of the file or create a new short file. When the provided argument is a directory, it will return the information that it is a directory. If a link is given, it will try to obtain the File content pointed by the the link. If the argument starts with a `>`, it will create a file under the working directory with default user permission `-rw-r--r--`.
10. ln \[-s\] \[source\] \[target\] <br/>
ln command is used to create a hard link or a symbolic link to an existing file. Source is for the source file, and target is for the link. Without specifying `-s` option, it is creating a hard link, which points to the same inode(file content). With the `-s` option, it is creating a symlink, which refer to the source file by name.
11. extcluster <br/>
extcluster command is used to analyze the count and average size of the file group by the user-level file type start from the current working directory.  
12. quit <br/>
quit command is used to end the CLI session.





















