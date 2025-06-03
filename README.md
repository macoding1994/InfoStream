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