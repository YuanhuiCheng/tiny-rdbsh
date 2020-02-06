# Unix Dumb File System

[useful link](https://www.mkssoftware.com/docs/man1/ls.1.asp)

### Relation Schema
**1. file=(id, type, op, gp, tp, numOfLinks, ownerID, groupID, size, time, name, parentID)**

_attributes_:
- id: auto-incremental number
- permission (now decomposed into `type`, `owner permission (op)`, `group permission (gp)`, `other permission (tp)`)
    - **10** characters in total
    - first character represents the type (e.g. d -> directory, - -> regular file)
    - The next nine characters are in three groups of three; they describe the permissions on the file. The first group of three describes owner permissions; the second describes group permissions; the third describes other (or world) permissions. 
- numOfLinks: the number of hard links to a particular inode
- ownerID: id of owner (the name of the owner of the file or directory)
- groupID: id of group (the name of the group that owns the file or directory)
- size: the size of the file, expressed in bytes
- time: For a file, this is the time that the file was last changed; for a directory, it is the time that the directory was created
- name
- parentID

or use another relation schema:
file=(id, type, or, ow, ox, gr, gw, gr, tw, tx, tr, numOfLinks, ownerID, groupID, size, time, name, parentID)

_note_: 
- sometimes, the owner is not name but ID(number) and `<unavail>` (maybe we are not supposed to consider this dumb case).
- what does the last character `@` from `-rw-r--r--@` mean?
- permission characters:
    r    Permission to read file
    w    Permission to write to file
    x    Permission to execute file
    <!-- [a    Archive bit is on (file has not been backed up)
    c    Compressed file
    s    System file
    h    Hidden file
    t    Temporary file] <- what hack does these mean?> -->
- **we may add more user-level file types (for ex: C, C++, text, executable ...)**

**2. fileType=(id, type)**

_attributes_:    

id | type 
--- | --- 
\- | Regular file 
b | Block special file 
c | Character special file 
d | Directory 
l | Symbolic link 
n | Network file 
p | FIFO 
s | Socket 
    
**3. permissionType=(id, pr, pw, pe)**

_attributes_:
- id
- pr: permission to read
- pw: permission to write
- pe: permission to execute

id | pr | pw | pe 
--- | --- | --- | ---
0 | - | - | -
1 | - | - | x
2 | - | w | -
3 | - | w | x
4 | r | - | -
5 | r | - | x
6 | r | w | -
7 | r | w | x 

_note_: we should use `bits` or `decimal` to be the id?

_references_:
7	read, write and execute	rwx	111 <br />
6	read and write	rw-	110 <br />
5	read and execute	r-x	101 <br />
4	read only	r--	100 <br />
3	write and execute	-wx	011 <br />
2	write only	-w-	010 <br />
1	execute only	--x	001 <br />
0	none	---	000 

**4. owner=(id, name)**

**5. group=(id, name)**

**6. pathVar=(var, path, fileID)**

_attributes_: 
- var: environment variable
- path: corresponding path
- fileID

_note_: 
- needs to run echo $PATH to get PATH variables,
- also, needs to look at .bashrc and .zshrc to get more variables
- all files can only be found under PATH variables

[useful link](https://www.cs.purdue.edu/homes/bb/cs348/www-S08/unix_path.html)

**7. symbolicLink=(pfID, fID)**

_attributes_: 
- pfID: fileID of pointed file 
- fID: who directs the link

_note_:
- to find sybolic link: ls -la [some path] | grep "\->"
- may store path?

**8. hardLink=(inode, fID)**

_attributes_: 
- inode: inode's Id
- fID: who directs the link

_note_:
- to find hard link: ls -l, ls -i (needs to do more research)
- hard link can only link files
