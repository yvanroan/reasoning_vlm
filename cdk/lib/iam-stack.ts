import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class IamStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create an IAM group for developers
    const developersGroup = new iam.Group(this, 'DevelopersGroup', {
      groupName: 'Developers',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('ReadOnlyAccess'),
      ],
    });

    // Create a custom policy for S3 access
    const s3AccessPolicy = new iam.Policy(this, 'S3AccessPolicy', {
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            's3:GetObject',
            's3:PutObject',
            's3:ListBucket',
          ],
          resources: [
            'arn:aws:s3:::reasoning-vlm-image-upload/*',
            'arn:aws:s3:::reasoning-vlm-image-upload',
            'arn:aws:s3:::reasoning-vlm-processed-images/*',
            'arn:aws:s3:::reasoning-vlm-processed-images',
          ],
        }),
      ],
    });

    // Attach the S3 policy to the developers group
    developersGroup.attachInlinePolicy(s3AccessPolicy);

    // Create an IAM user
    const developer = new iam.User(this, 'Developer', {
      userName: 'developer',
      groups: [developersGroup],
    });

    // Create access key for the user
    const accessKey = new iam.AccessKey(this, 'DeveloperAccessKey', {
      user: developer,
    });

    // Output the access key information
    new cdk.CfnOutput(this, 'AccessKeyId', {
      value: accessKey.accessKeyId,
      description: 'The access key ID for the developer user',
    });

    new cdk.CfnOutput(this, 'SecretAccessKey', {
      value: accessKey.secretAccessKey.unsafeUnwrap(),
      description: 'The secret access key for the developer user',
    });
  }
}
