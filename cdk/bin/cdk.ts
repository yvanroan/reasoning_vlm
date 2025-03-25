#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { S3Stack } from '../lib/s3-stack';
import { IamStack } from '../lib/iam-stack';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables
const envPath = path.join(__dirname, '../../.env');
console.log('Loading .env from:', envPath);
dotenv.config({ path: envPath });


const app = new cdk.App();

// Try environment variables in order of preference
const env = { 
  account: process.env.AWS_ACCOUNT,
  region: process.env.AWS_REGION
};

// Better error message showing which variables are missing
if (!env.account || !env.region) {
  console.error('Environment Configuration Error:');
  if (!env.account) console.error('- AWS_ACCOUNT is not set');
  if (!env.region) console.error('- AWS_REGION is not set');
  console.error('\nPlease set these variables in your .env file or configure AWS CLI');
  process.exit(1);
}

// Deploy the S3 stack
new S3Stack(app, 'S3Stack', { env });

// Deploy the IAM stack
new IamStack(app, 'IamStack', { env });
