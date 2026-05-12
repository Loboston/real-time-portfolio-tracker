import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { InfraStack } from './infra-stack';

export class ServicesStack extends cdk.Stack {
  constructor(scope: Construct, id: string, infra: InfraStack, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── ECS Cluster ───────────────────────────────────────────────────────
    const cluster = new ecs.Cluster(this, 'Cluster', { vpc: infra.vpc });

    // ── Backend Task Definition ───────────────────────────────────────────
    const backendTaskDef = new ecs.FargateTaskDefinition(this, 'BackendTask', {
      memoryLimitMiB: 512,
      cpu: 256,
    });

    infra.backendRepo.grantPull(backendTaskDef.obtainExecutionRole());
    infra.dbSecret.grantRead(backendTaskDef.obtainExecutionRole());
    infra.appSecret.grantRead(backendTaskDef.obtainExecutionRole());

    const backendLog = new logs.LogGroup(this, 'BackendLogs', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    backendTaskDef.addContainer('backend', {
      image: ecs.ContainerImage.fromEcrRepository(infra.backendRepo, 'latest'),
      portMappings: [{ containerPort: 8000 }],
      environment: {
        REDIS_URL: `redis://${infra.redisHost}:6379/0`,
        DB_HOST: infra.dbHost,
        DB_NAME: 'portfolio_db',
        ENVIRONMENT: 'production',
      },
      secrets: {
        SECRET_KEY: ecs.Secret.fromSecretsManager(infra.appSecret),
        DB_USER: ecs.Secret.fromSecretsManager(infra.dbSecret, 'username'),
        DB_PASSWORD: ecs.Secret.fromSecretsManager(infra.dbSecret, 'password'),
        POLYGON_API_KEY: ecs.Secret.fromSecretsManagerVersion(
          secretsmanager.Secret.fromSecretNameV2(this, 'PolygonSecret', 'portfolio-tracker/polygon-api-key'),
          { versionStage: 'AWSCURRENT' },
        ),
      },
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'backend', logGroup: backendLog }),
    });

    // ── Frontend Task Definition ──────────────────────────────────────────
    const frontendTaskDef = new ecs.FargateTaskDefinition(this, 'FrontendTask', {
      memoryLimitMiB: 512,
      cpu: 256,
    });

    infra.frontendRepo.grantPull(frontendTaskDef.obtainExecutionRole());

    const frontendLog = new logs.LogGroup(this, 'FrontendLogs', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    frontendTaskDef.addContainer('frontend', {
      image: ecs.ContainerImage.fromEcrRepository(infra.frontendRepo, 'latest'),
      portMappings: [{ containerPort: 80 }],
      logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'frontend', logGroup: frontendLog }),
    });

    // ── ALB ───────────────────────────────────────────────────────────────
    const alb = new elbv2.ApplicationLoadBalancer(this, 'Alb', {
      vpc: infra.vpc,
      internetFacing: true,
      securityGroup: infra.albSg,
    });

    const listener = alb.addListener('HttpListener', { port: 80, open: true });

    // ── Backend Service ───────────────────────────────────────────────────
    const backendService = new ecs.FargateService(this, 'BackendService', {
      cluster,
      taskDefinition: backendTaskDef,
      desiredCount: 1,
      securityGroups: [infra.appSg],
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    });

    listener.addTargets('BackendTarget', {
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [backendService],
      priority: 10,
      conditions: [
        elbv2.ListenerCondition.pathPatterns(['/api/*', '/ws/*', '/docs', '/openapi.json', '/health']),
      ],
      healthCheck: { path: '/health', interval: cdk.Duration.seconds(30) },
    });

    // ── Frontend Service ──────────────────────────────────────────────────
    const frontendService = new ecs.FargateService(this, 'FrontendService', {
      cluster,
      taskDefinition: frontendTaskDef,
      desiredCount: 1,
      securityGroups: [infra.appSg],
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
    });

    listener.addTargets('FrontendTarget', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targets: [frontendService],
      healthCheck: { path: '/', interval: cdk.Duration.seconds(30) },
    });

    // ── CloudFront Distribution ───────────────────────────────────────────
    const albOrigin = new origins.LoadBalancerV2Origin(alb, {
      protocolPolicy: cloudfront.OriginProtocolPolicy.HTTP_ONLY,
      httpPort: 80,
    });

    const noCachePolicy = new cloudfront.CachePolicy(this, 'NoCachePolicy', {
      defaultTtl: cdk.Duration.seconds(0),
      minTtl: cdk.Duration.seconds(0),
      maxTtl: cdk.Duration.seconds(0),
    });

    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: albOrigin,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: noCachePolicy,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
      },
      additionalBehaviors: {
        '/ws/*': {
          origin: albOrigin,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: noCachePolicy,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
    });

    // ── Outputs ───────────────────────────────────────────────────────────
    new cdk.CfnOutput(this, 'AppUrl', { value: `https://${distribution.distributionDomainName}` });
  }
}
