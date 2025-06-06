# InfoStream

**The Scenario:** "InfoStream," a content aggregation startup, wants to build a platform that fetches news articles from various (mock) external RSS feeds, processes them (e.g., basic keyword tagging – can be simulated), and displays them to users via a simple web interface. They want to build this using a microservices architecture.

**Key Tasks:**

1. Design the Infrastructure: Create     a VPC designed for microservice communication.

2. Microservices: 

3. - Feed-Fetcher Service: A      Dockerized service (e.g., Python with feedparser) that periodically fetches data from 2-3 mock RSS      feeds.
   - Processing Service: A Dockerized      service that takes fetched content, performs mock "keyword      tagging" (e.g., adds some predefined tags based on content), and      stores it.
   - API/Frontend Service: A      Dockerized service that provides an API to retrieve processed articles      and a very simple web page to display them.

4. Container Orchestration     (Simplified): 

5. - Deploy each microservice as      Docker containers on separate EC2 instances (or multiple containers on      fewer instances if resources are a concern).
   - Services should communicate with      each other over the network (internal to the VPC).

6. Storage: 

7. - Use S3 for storing raw fetched      content or logs.
   - Use a simple database (RDS or      alternative as in Scenario 1) to store processed articles and tags.

8. Load Balancing: 

9. - Implement an Application Load      Balancer for the API/Frontend Service.
   - Consider if internal load      balancing between services is necessary/feasible (might be an advanced      topic for 2 weeks).

10. Security: 

11. - Secure inter-service      communication (Security Groups).
    - Secure the public-facing      API/Frontend service.

12. Topology: Create a detailed     network and service interaction diagram.

**Expected Focus:** Implementing a basic microservices architecture, inter-service communication, and containerization of different application components.



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
