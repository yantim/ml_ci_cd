# AWS Infrastructure Deployment

This guide covers deploying the ML CI/CD pipeline to AWS using Terraform.

## 🏗️ Infrastructure Overview

The AWS deployment includes:

- **ECS Cluster**: Container orchestration for model serving
- **RDS PostgreSQL**: MLflow backend store
- **S3 Bucket**: MLflow artifact store and data storage
- **ECR Repository**: Docker image registry
- **Application Load Balancer**: Traffic distribution and SSL termination
- **VPC**: Isolated network environment
- **IAM Roles**: Secure access controls

## 📋 Prerequisites

### Required Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-west-2)
# - Default output format (json)

# Verify configuration
aws sts get-caller-identity
```

## 🚀 Deployment Steps

### 1. Configure Terraform Variables

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# Project Configuration
project_name = "ml-cicd-pipeline"
environment  = "production"
region      = "us-west-2"

# Network Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-west-2a", "us-west-2b"]

# Database Configuration
db_instance_class = "db.t3.micro"
db_name          = "mlflow"
db_username      = "mlflow_user"
db_password      = "your-secure-password"  # Use AWS Secrets Manager in production

# ECS Configuration
ecs_task_cpu    = 512
ecs_task_memory = 1024
desired_count   = 2

# Domain Configuration (optional)
domain_name = "your-domain.com"
```

### 2. Initialize and Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan deployment
terraform plan

# Apply infrastructure (review plan first!)
terraform apply
```

### 3. Build and Push Docker Images

```bash
# Build images
make build-images

# Tag and push to ECR
make push-images
```

### 4. Deploy Application

```bash
# Deploy to ECS
make deploy-aws

# Check deployment status
aws ecs describe-services --cluster ml-cicd-cluster --services ml-model-service
```

## 📊 Infrastructure Components

### VPC and Networking

```mermaid
graph TB
    subgraph "VPC (10.0.0.0/16)"
        subgraph "Public Subnets"
            ALB[Application Load Balancer]
            NAT[NAT Gateway]
        end
        
        subgraph "Private Subnets"
            ECS[ECS Tasks]
            RDS[RDS PostgreSQL]
        end
        
        subgraph "Availability Zone A"
            PubA[Public Subnet A]
            PrivA[Private Subnet A]
        end
        
        subgraph "Availability Zone B"
            PubB[Public Subnet B]
            PrivB[Private Subnet B]
        end
    end
    
    Internet --> ALB
    ALB --> ECS
    ECS --> RDS
    ECS --> S3[S3 Bucket]
```

### Security Groups

- **ALB Security Group**: HTTP/HTTPS from internet
- **ECS Security Group**: HTTP from ALB only  
- **RDS Security Group**: PostgreSQL from ECS only

### IAM Roles

- **ECS Task Role**: Access to S3, RDS, and logging
- **ECS Execution Role**: Pull images from ECR
- **EC2 Instance Role**: ECS agent permissions

## 🔧 Configuration Management

### Environment Variables

The deployment uses AWS Systems Manager Parameter Store for configuration:

```bash
# Set MLflow configuration
aws ssm put-parameter \
  --name "/ml-cicd/mlflow/backend-store-uri" \
  --value "postgresql://username:password@rds-endpoint:5432/mlflow" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/ml-cicd/mlflow/artifact-root" \
  --value "s3://your-mlflow-bucket/artifacts" \
  --type "String"
```

### Secrets Management

Use AWS Secrets Manager for sensitive data:

```bash
# Store database credentials
aws secretsmanager create-secret \
  --name "ml-cicd/database" \
  --description "Database credentials" \
  --secret-string '{"username":"mlflow_user","password":"your-secure-password"}'
```

## 📈 Monitoring and Logging

### CloudWatch Integration

```bash
# View ECS service logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/ml-model-service"

# Stream logs
aws logs tail /ecs/ml-model-service --follow
```

### Metrics and Alarms

The infrastructure automatically creates:

- **ECS Service Utilization**: CPU and memory metrics
- **ALB Health**: Request count and latency
- **RDS Performance**: Connection count and query performance
- **Custom Application Metrics**: Model inference metrics

## 🔄 CI/CD Integration

### GitHub Actions Deployment

The `.github/workflows/deploy.yml` workflow automatically:

1. Builds Docker images
2. Pushes to ECR
3. Updates ECS service
4. Runs health checks

Required GitHub Secrets:
```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
ECR_REPOSITORY_URI
ECS_CLUSTER_NAME
ECS_SERVICE_NAME
```

## 🛡️ Security Best Practices

### Network Security
- All resources in private subnets except ALB
- Security groups with minimal required access
- VPC Flow Logs enabled for monitoring

### Access Control
- IAM roles with least privilege principle
- No hardcoded credentials in code
- Secrets stored in AWS Secrets Manager

### Data Protection
- RDS encryption at rest enabled
- S3 bucket encryption enabled
- SSL/TLS termination at ALB

## 💰 Cost Optimization

### Resource Sizing
- Start with t3.micro for RDS
- Use Fargate Spot for non-critical workloads
- Enable ECS auto-scaling

### Storage Optimization
- S3 Intelligent Tiering for MLflow artifacts
- Regular cleanup of old model artifacts
- Use S3 lifecycle policies

## 🔧 Maintenance

### Updates and Patches
```bash
# Update infrastructure
terraform plan
terraform apply

# Update application
make deploy-aws

# Database maintenance
aws rds describe-pending-maintenance-actions
```

### Backup and Recovery
- RDS automated backups (7-day retention)
- S3 versioning enabled for artifacts
- Infrastructure code in version control

## 🚨 Troubleshooting

### Common Deployment Issues

**ECS Task Fails to Start:**
```bash
# Check ECS task logs
aws ecs describe-tasks --cluster ml-cicd-cluster --tasks <task-arn>

# Check CloudWatch logs
aws logs tail /ecs/ml-model-service --follow
```

**Database Connection Issues:**
```bash
# Test database connectivity
aws rds describe-db-instances --db-instance-identifier ml-cicd-database

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

**Load Balancer Health Checks Failing:**
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>

# Verify health check configuration
aws elbv2 describe-target-groups --target-group-arns <target-group-arn>
```

### Cleanup

To destroy the infrastructure:
```bash
# Warning: This will delete all resources!
terraform destroy
```

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Security Guide](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.html)
