# Unix Dumb File System (RDBSH)

### Tasks
- Entity-relationship model + description (submit pdf)
- populate your database with real-world sample 
- add primary key/foreign key/ + add indexes (finally) (submit sql code)
- Prototype client (code + readme)
- video (~ 5 min)

#### Required Utilities
- keep track of the current working directory
- cd 
- execute any executable program that is in the PATH
- ls
- ls -l
- find: accpets direcotry and (partial) file name
- find xxx -ls
- grep: accepts the (partial) file anme and seek the relevant pattern; output the line number and line for mathching lines (it can only search plain-text file) 

#### Optional additional Utilities 
- get more file types in application and user-level to store (abandoned)

Read:
- pwd 
- head (head -n) / tail (tail -n)

Write:
- mkdir / rmdir (rm -r) (creating and copying files are tricky as they require to consider the `inode` to be added, or we can ignore it)
- touch
- rm (`rm` is tricky as it requires to consider inode, soft(symbolic) link and hard link)
- cp
- mv
- ln (`I recommend to do this one`)
    - ln [file] [hard-link-to-file] (the `hard-link-to-file` would refer the same inode as `file` in `hardLink_t`)
    - ln -s [file] [soft-link-to-file] (add new entry in `symbolicLink_t`)
- sed (replace or substitute string, this one is also good)

Ownership:
- chmod
- chown