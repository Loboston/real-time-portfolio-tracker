import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

export class InfraStack extends cdk.Stack {
  // Expose these so ServicesStack can reference them
  public readonly vpc: ec2.Vpc;
  public readonly appSg: ec2.SecurityGroup;
  public readonly albSg: ec2.SecurityGroup;
  public readonly dbSecret: secretsmanager.Secret;
  public readonly appSecret: secretsmanager.Secret;
  public readonly redisHost: string;
  public readonly dbHost: string;
  public readonly backendRepo: ecr.Repository;
  public readonly frontendRepo: ecr.Repository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── VPC ──────────────────────────────────────────────────────────────
    this.vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 1,
    });

    // ── Security Groups ───────────────────────────────────────────────────
    const dbSg = new ec2.SecurityGroup(this, 'DbSg', { vpc: this.vpc });
    const redisSg = new ec2.SecurityGroup(this, 'RedisSg', { vpc: this.vpc });
    this.appSg = new ec2.SecurityGroup(this, 'AppSg', { vpc: this.vpc });
    this.albSg = new ec2.SecurityGroup(this, 'AlbSg', { vpc: this.vpc, allowAllOutbound: true });

    this.albSg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(80), 'HTTP from internet');
    this.appSg.addIngressRule(this.albSg, ec2.Port.tcp(8000), 'From ALB to backend');
    this.appSg.addIngressRule(this.albSg, ec2.Port.tcp(80), 'From ALB to frontend');
    dbSg.addIngressRule(this.appSg, ec2.Port.tcp(5432), 'Postgres from app');
    redisSg.addIngressRule(this.appSg, ec2.Port.tcp(6379), 'Redis from app');

    // ── RDS Postgres ──────────────────────────────────────────────────────
    this.dbSecret = new secretsmanager.Secret(this, 'DbSecret', {
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'portfolio' }),
        generateStringKey: 'password',
        excludePunctuation: true,
      },
    });

    const db = new rds.DatabaseInstance(this, 'Postgres', {
      engine: rds.DatabaseInstanceEngine.postgres({ version: rds.PostgresEngineVersion.VER_16 }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
      vpc: this.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [dbSg],
      credentials: rds.Credentials.fromSecret(this.dbSecret),
      databaseName: 'portfolio_db',
      deletionProtection: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.dbHost = db.dbInstanceEndpointAddress;

    // ── ElastiCache Redis ─────────────────────────────────────────────────
    const redisSubnetGroup = new elasticache.CfnSubnetGroup(this, 'RedisSubnetGroup', {
      description: 'Redis subnet group',
      subnetIds: this.vpc.privateSubnets.map((s) => s.subnetId),
    });

    const redis = new elasticache.CfnCacheCluster(this, 'Redis', {
      cacheNodeType: 'cache.t3.micro',
      engine: 'redis',
      numCacheNodes: 1,
      cacheSubnetGroupName: redisSubnetGroup.ref,
      vpcSecurityGroupIds: [redisSg.securityGroupId],
    });

    this.redisHost = redis.attrRedisEndpointAddress;

    // ── ECR Repositories ──────────────────────────────────────────────────
    this.backendRepo = new ecr.Repository(this, 'BackendRepo', {
      repositoryName: 'portfolio-tracker-backend',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    this.frontendRepo = new ecr.Repository(this, 'FrontendRepo', {
      repositoryName: 'portfolio-tracker-frontend',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: true,
    });

    // ── App Secret Key ────────────────────────────────────────────────────
    this.appSecret = new secretsmanager.Secret(this, 'AppSecret', {
      generateSecretString: { excludePunctuation: false, passwordLength: 64 },
    });

    // ── Outputs ───────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'BackendEcr', { value: this.backendRepo.repositoryUri });
    new cdk.CfnOutput(this, 'FrontendEcr', { value: this.frontendRepo.repositoryUri });
  }
}
