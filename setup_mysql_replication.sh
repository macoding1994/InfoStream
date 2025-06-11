#!/bin/bash
set -e

# 从环境变量获取配置
MASTER_CONTAINER="mysql-master"
SLAVE_CONTAINER="mysql-slave"
MASTER_IP="172.31.38.247"
MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD:-"infostream_pass"}
REPLICA_USER=${MYSQL_USER:-"infostream_user"}
REPLICA_PASSWORD=${MYSQL_PASSWORD:-"infostream_pass"}
DATABASE=${MYSQL_DATABASE:-"infostream_db"}
MAX_RETRIES=5
RETRY_INTERVAL=10

echo "🔧 开始配置MySQL主从复制..."

# 1. 检查容器是否运行
check_container() {
    local container=$1
    if ! sudo docker ps | grep -q $container; then
        echo "❌ 容器 $container 未运行!"
        exit 1
    fi
}

check_container $MASTER_CONTAINER
check_container $SLAVE_CONTAINER

# 2. 在master上创建复制用户
echo "🔑 在master上创建复制用户..."
sudo docker exec -i $MASTER_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "
CREATE USER IF NOT EXISTS '$REPLICA_USER'@'%' IDENTIFIED BY '$REPLICA_PASSWORD';
GRANT REPLICATION SLAVE ON *.* TO '$REPLICA_USER'@'%';
FLUSH PRIVILEGES;
"

# 3. 配置GTID复制
echo "⚙️ 配置GTID复制..."
sudo docker exec -i $MASTER_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "
SET @@GLOBAL.ENFORCE_GTID_CONSISTENCY = ON;
SET @@GLOBAL.GTID_MODE = ON;
SET @@GLOBAL.SERVER_ID = 1;
"

sudo docker exec -i $SLAVE_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "
SET @@GLOBAL.ENFORCE_GTID_CONSISTENCY = ON;
SET @@GLOBAL.GTID_MODE = ON;
SET @@GLOBAL.SERVER_ID = 2;
"

# 4. 重置从库GTID状态
echo "🔄 重置从库GTID状态..."
sudo docker exec -i $SLAVE_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "RESET MASTER;"

# 5. 初始数据同步
echo "🔄 执行初始数据同步(使用mysqldump从主库导出数据并导入从库)..."
sudo docker exec -i $MASTER_CONTAINER mysqldump -uroot -p$MYSQL_ROOT_PASSWORD --single-transaction --master-data=2 $DATABASE | \
sudo docker exec -i $SLAVE_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD $DATABASE

# 6. 配置slave
echo "⚙️ 配置slave复制..."
for ((i=1; i<=$MAX_RETRIES; i++)); do
    if sudo docker exec -i $SLAVE_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "
    STOP SLAVE;
    CHANGE MASTER TO
    MASTER_HOST='$MASTER_IP',
    MASTER_USER='$REPLICA_USER',
    MASTER_PASSWORD='$REPLICA_PASSWORD',
    MASTER_AUTO_POSITION=1;
    START SLAVE;
    "; then
        break
    fi
    echo "⚠️ 尝试 $i/$MAX_RETRIES 失败，等待 $RETRY_INTERVAL 秒后重试..."
    sleep $RETRY_INTERVAL
done

# 7. 检查复制状态
echo "🔍 检查复制状态..."
slave_status=$(sudo docker exec -i $SLAVE_CONTAINER mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "SHOW SLAVE STATUS\G")

if echo "$slave_status" | grep -q "Slave_IO_Running: Yes" && \
   echo "$slave_status" | grep -q "Slave_SQL_Running: Yes"; then
    echo "✅ 主从复制配置成功!"
    echo "Master: $MASTER_CONTAINER"
    echo "Slave: $SLAVE_CONTAINER"
    echo "Database: $DATABASE"
else
    echo "❌ 复制配置失败!"
    echo "$slave_status"
    exit 1
fi
