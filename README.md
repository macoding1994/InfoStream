# InfoStream

### Feed-Fetcher Service

### Processing Service

### API Service

| API Endpoint               | Method | Purpose                                                      |
| -------------------------- | ------ | ------------------------------------------------------------ |
| `/api/feeds_with_keywords` | GET    | Retrieve list of feed articles with keywords, with pagination |
| `/trigger_fetch`           | POST   | Trigger background task to fetch RSS feed articles and store them in the database |
| `/trigger_tag`             | POST   | Trigger background task to extract keywords for untagged feeds and store them |
| `/test_backend`            | GET    | Test whether the backend server is online and functioning correctly |

### 部署过程命令

```shell
sed -i 's/\r//' start.sh crontab setup_mysql_replication.sh

docker-compose -f docker-compose.nginx.yml up -d
docker-compose -f docker-compose.redis-mysql.yml up -d
docker-compose -f docker-compose.web.yml build && docker-compose -f docker-compose.web.yml up -d
docker-compose -f docker-compose.fetcher.yml build && docker-compose -f docker-compose.fetcher.yml up -d
docker-compose -f docker-compose.tagger.yml build && docker-compose -f docker-compose.tagger.yml up -d
sh setup_mysql_replication.sh


docker-compose -f docker-compose.web.yml down -v
docker-compose -f docker-compose.redis-mysql.yml down -v
docker-compose -f docker-compose.nginx.yml down -v
docker-compose -f docker-compose.fetcher.yml down -v
docker-compose -f docker-compose.tagger.yml down -v


```



### EC2 Common Commands

```shell
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

docker-compose --version

sudo apt update -y
sudo apt install unzip curl -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version


cd /home/ubuntu
git clone https://github.com/macoding1994/InfoStream.git
cd /home/ubuntu/InfoStream

```



### MYSQL master-slave configuration

```shell
# master
[mysqld]
bind-address = 0.0.0.0
server-id = 1
gtid-mode = ON
enforce-gtid-consistency = ON
log-bin = mysql-bin
binlog-format = ROW
skip-name-resolve

# slave
[mysqld]
bind-address = 0.0.0.0
server-id = 2
gtid-mode = ON
enforce-gtid-consistency = ON
log-bin = mysql-bin
binlog-format = ROW
skip-name-resolve
```




| 项目         | Application Load Balancer (ALB)          | Network Load Balancer (NLB)           |
| ------------ | ---------------------------------------- | ------------------------------------- |
| 主要用途     | 应用层（第7层，HTTP/HTTPS）负载均衡      | 网络层（第4层，TCP/UDP）负载均衡      |
| 适合场景     | 网站、API服务器，按URL、域名分流         | 高性能 TCP 流量（游戏、视频、数据库） |
| 转发能力     | 可以根据 URL 路由规则、Host 头、路径转发 | 只做 TCP/UDP 连接转发，不看上层协议   |
| 延迟         | 稍高（有 HTTP 处理）                     | 极低（直通 TCP）                      |
| 监控         | 支持 HTTP 状态码健康检查                 | 支持 TCP 端口健康检查                 |
| 静态 IP 支持 | 否，ALB 会动态分配 IP                    | 是，NLB 支持固定 IP                   |
| HTTPS 终止   | 支持，ALB 可以直接做 SSL/TLS 终止        | 通常不处理 SSL/TLS，直接转发到后端    |
| 价格         | 一般比 NLB 稍贵                          | 比 ALB 更便宜些，特别适合高频 TCP     |
