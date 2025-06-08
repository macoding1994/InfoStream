# InfoStream

**The Scenario:** "InfoStream," a content aggregation startup, wants to build a platform that fetches news articles from various (mock) external RSS feeds, processes them (e.g., basic keyword tagging – can be simulated), and displays them to users via a simple web interface. They want to build this using a microservices architecture.



### 部署过程命令

```shell
sed -i 's/\r//' start.sh crontab

docker-compose -f docker-compose.nginx.yml up -d
docker-compose -f docker-compose.redis-mysql.yml up -d
docker-compose -f docker-compose.web.yml build && docker-compose -f docker-compose.web.yml up -d
docker-compose -f docker-compose.fetcher.yml build && docker-compose -f docker-compose.fetcher.yml up -d
docker-compose -f docker-compose.tagger.yml build && docker-compose -f docker-compose.tagger.yml up -d

docker-compose -f docker-compose.redis-mysql.yml down -v


```



### 启动队列任务

```shell
# 启动 fetcher 队列的 worker
celery -A app.celery worker --loglevel=info -Q fetcher

# 启动 tagger 队列的 worker
celery -A app.celery worker --loglevel=info -Q tagger

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

docker-compose --version


sed -i 's/\r//' start.sh crontab
docker-compose build && docker-compose up
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
