# InfoStream

| **Name**                 | **Metric ID** |
| ------------------------ | ------------- |
| Koh Cheng Tsuang, Daniel | 22101920      |
| Pang Teng Xuan           | 24065073      |
| MA SHANGJU               | 23110836      |

### Feed-Fetcher Service

The Feed Fetcher is a Celery background task that automatically **retrieves articles from a set of predefined RSS/Atom feeds**.

- It parses the feed entries from multiple feed URLs (defined in `FEED_DICT`).
- For each article, it extracts the URL, title, and description.
- The article data is stored in the `feeds` table of the database.
- If the feed URL is mapped to a feed class (category), this information is also stored as a keyword.

### Processing Service

This Celery task is used to **automatically tag unprocessed feed articles** with keywords.

- It queries the database for feeds that are not yet tagged (`is_tagged = 0`).
- For each untagged feed, it calls the **DeepSeek API** to extract relevant keywords from the feed URL.
- It inserts these keywords into the `keyword` table.
- Finally, it marks the feed as `is_tagged = 1` to indicate it has been processed.

This task helps keep your feed database **enriched with meaningful tags** so that front-end applications can show categorized or searchable feed content.

### API Service

| API Endpoint               | Method | Purpose                                                      |
| -------------------------- | ------ | ------------------------------------------------------------ |
| `/api/feeds_with_keywords` | GET    | Retrieve list of feed articles with keywords, with pagination |
| `/trigger_fetch`           | POST   | Trigger background task to fetch RSS feed articles and store them in the database |
| `/trigger_tag`             | POST   | Trigger background task to extract keywords for untagged feeds and store them |
| `/test_backend`            | GET    | Test whether the backend server is online and functioning correctly |

### Elastic Load Balancer（ALB）

An **Application Load Balancer (ALB)** named **InfoStream** was created on AWS to distribute incoming traffic.
 The load balancer’s DNS is:
 `InfoStream-124212143.us-east-1.elb.amazonaws.com`.

A **target group** was configured to forward traffic on **port 80** to two EC2 instances:
 **InfoStream-frontend1** and **InfoStream-frontend**.

This setup ensures that HTTP requests are balanced across the frontend services, providing better availability and scalability for the application.

### S3

An **automated log archival workflow** was implemented using Amazon S3.
 A **shell script** was scheduled via **cron** to periodically upload Docker container logs to an S3 bucket named **`cloud-sec-msj`**.

The EC2 instance was assigned the **`EMR_EC2_DefaultRole`** IAM role, providing the necessary permissions to upload logs to S3 securely, without hardcoding AWS credentials.

This solution ensures that container logs are reliably archived in S3, supporting future monitoring, troubleshooting, and compliance requirements.



### Commands

```shell

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
sudo docker-compose -f docker-compose.nginx.yml up -d

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

