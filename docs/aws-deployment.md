# PocketSmart AI - AWS Deployment Roadmap

## Future Production Architecture
1. **Frontend Hosting**: AWS S3 Static Website Hosting + CloudFront CDN + Route 53 (SSL/TLS via ACM).
2. **Backend Services**: AWS ECS (Fargate) or AWS App Runner for containerized FastAPI deployment.
3. **Database**: Amazon RDS for PostgreSQL (Multi-AZ for high availability).
4. **Secrets Management**: AWS Secrets Manager or Parameter Store for API keys and JWT secrets.
5. **Object Storage**: AWS S3 Bucket for uploaded outfit images with presigned URLs.
