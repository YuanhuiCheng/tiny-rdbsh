SQL_USER_NAME=$1
SQL_USER_PWD=$2

IMAGE_NAME="yellow82cheng/ubuntu-dog"
CONTAINER_NAME="lightu"
WKR_ROOT_DIR="/"
EXTRACT_UNIX_PROP_PY_NAME="extract_unix_prop.py"
MYSQL_CONN_EXE_PY_NAME="mysql_exe.py"
RDBSH_DB_NAME="rdbsh"
RDBSH_CONTENTS_DB_NAME="rdbshfile"
TEMP_UNIX_DIR="temp_unix"
RDBSH_EXECUTABLE_SQL="setupUNIXDB.sql"
FILE_CONTENT_TABLE_NAME="fileContent_t"

if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
        docker start $CONTAINER_NAME
    else
        # run your container
        docker run -t -d --name $CONTAINER_NAME $IMAGE_NAME
    fi
fi

docker cp $EXTRACT_UNIX_PROP_PY_NAME $CONTAINER_NAME:/
docker exec -it $CONTAINER_NAME /bin/sh -c "
    rm -rf csv/
    chown root:root $EXTRACT_UNIX_PROP_PY_NAME
    python3 $EXTRACT_UNIX_PROP_PY_NAME $WKR_ROOT_DIR
"

rm -rf err/
rm -rf csv/
rm -rf helpercsv/
rm -rf ../final/csv/
docker cp $CONTAINER_NAME:/err .
docker cp $CONTAINER_NAME:/csv .
docker cp $CONTAINER_NAME:/helpercsv .
docker cp $CONTAINER_NAME:/csv ../final/

rm -rf $TEMP_UNIX_DIR 
mkdir -p $TEMP_UNIX_DIR 

docker cp $CONTAINER_NAME:$WKR_ROOT_DIR $TEMP_UNIX_DIR

cd ../final/

# don't forget to create a database first
mysql --user=$SQL_USER_NAME --password=$SQL_USER_PWD --execute="source $RDBSH_EXECUTABLE_SQL;" --local-infile=true
echo "rdbsh system finished"

cd ../move_unix_box

python3 mysql_exe.py $SQL_USER_NAME $SQL_USER_PWD
echo "rdbsh file load finished"

mysqldump -u$SQL_USER_NAME -p$SQL_USER_PWD $RDBSH_DB_NAME $FILE_CONTENT_TABLE_NAME > ../final/file_contents/rdbsh_fileContent.sql
mysqldump -u$SQL_USER_NAME -p$SQL_USER_PWD $RDBSH_DB_NAME > ../${RDBSH_DB_NAME}.sql
echo "rdbsh dump finished"
