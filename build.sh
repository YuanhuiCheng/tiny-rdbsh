IMAGE_NAME="yellow82cheng/ubuntu-dog"
CONTAINER_NAME="lightu"
WKR_ROOT_DIR="/"

if [ ! "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$CONTAINER_NAME)" ]; then
        docker start $CONTAINER_NAME
    else
        # run your container
        docker run -t -d --name $CONTAINER_NAME $IMAGE_NAME
    fi
fi

docker cp __init__.py $CONTAINER_NAME:/
docker exec -it $CONTAINER_NAME /bin/sh -c "
    python3 __init__.py $WKR_ROOT_DIR
"
docker cp $CONTAINER_NAME:/csv .

# pip3 install mysql-connector-python-rf
# pip3 install mysql-connector-python
# python3 mysql_conn.py