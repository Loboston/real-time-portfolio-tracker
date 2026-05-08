#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { InfraStack } from '../lib/infra-stack';
import { ServicesStack } from '../lib/services-stack';

const app = new cdk.App();

const env = { account: '666715258708', region: 'us-east-1' };

const infra = new InfraStack(app, 'InfraStack', { env });
new ServicesStack(app, 'ServicesStack', infra, { env });
