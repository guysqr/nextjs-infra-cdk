from aws_cdk import (
    core,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_s3 as s3,
)


class ServerlessAppPipelineCdkStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline_name = "next-whtsqr"

        repo_name = "next-js-serverless-poc"
        repo_branch = "main"
        repo_owner = "guysqr"

        github_secret_arn = core.Fn.import_value("secrets-stack-GithubOAuthToken")

        state_bucket = s3.Bucket(
            self,
            "StateBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=False,
        )

        # policy for the serverless deploys
        serverless_deploy_policy = iam.PolicyStatement(
            actions=[
                "acm:DescribeCertificate",
                "acm:ListCertificates",
                "acm:RequestCertificate",
                "cloudfront:CreateCloudFrontOriginAccessIdentity",
                "cloudfront:CreateDistribution",
                "cloudfront:CreateInvalidation",
                "cloudfront:GetDistribution",
                "cloudfront:GetDistributionConfig",
                "cloudfront:ListCloudFrontOriginAccessIdentities",
                "cloudfront:ListDistributions",
                "cloudfront:ListDistributionsByLambdaFunction",
                "cloudfront:ListDistributionsByWebACLId",
                "cloudfront:ListFieldLevelEncryptionConfigs",
                "cloudfront:ListFieldLevelEncryptionProfiles",
                "cloudfront:ListInvalidations",
                "cloudfront:ListPublicKeys",
                "cloudfront:ListStreamingDistributions",
                "cloudfront:UpdateDistribution",
                "iam:AttachRolePolicy",
                "iam:CreateRole",
                "iam:CreateServiceLinkedRole",
                "iam:GetRole",
                "iam:PassRole",
                "iam:PutRolePolicy",
                "lambda:CreateFunction",
                "lambda:EnableReplication",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:GetFunctionConfiguration",
                "lambda:PublishVersion",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "route53:ChangeResourceRecordSets",
                "route53:ListHostedZonesByName",
                "route53:ListResourceRecordSets",
                "s3:CreateBucket",
                "s3:GetAccelerateConfiguration",
                "s3:GetObject",
                "s3:HeadBucket",
                "s3:ListBucket",
                "s3:PutAccelerateConfiguration",
                "s3:PutBucketPolicy",
                "s3:PutObject",
                "secretsmanager:GetSecretValue",
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW,
        )

        nextjs_serverless_build = codebuild.PipelineProject(
            self,
            "Build",
            project_name="build-proj-for-" + pipeline_name,
            environment_variables={
                "STATE_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=state_bucket.bucket_name
                )
            },
            cache=codebuild.Cache.bucket(s3.Bucket(self, "CacheBucket")),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_4_0
            ),
        )

        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact("BuildOutput")

        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name="pipeline-for-" + pipeline_name,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.GitHubSourceAction(
                            oauth_token=core.SecretValue.secrets_manager(
                                github_secret_arn, json_field="TOKEN"
                            ),
                            owner=repo_owner,
                            action_name="Github_Source",
                            repo=repo_name,
                            branch=repo_branch,
                            trigger=codepipeline_actions.GitHubTrigger.WEBHOOK,
                            output=source_output,
                        )
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="NextJs_Serverless_Build",
                            project=nextjs_serverless_build,
                            input=source_output,
                            outputs=[build_output],
                        ),
                    ],
                ),
            ],
        )

        nextjs_serverless_build.add_to_role_policy(statement=serverless_deploy_policy)

        core.CfnOutput(
            self,
            "PipelineArn",
            value=pipeline.pipeline_arn,
            export_name=self.stack_name + "-PipelineArn",
        )

        core.CfnOutput(
            self,
            "PipelineName",
            value=pipeline.pipeline_name,
            export_name=self.stack_name + "-PipelineName",
        )

        core.CfnOutput(
            self,
            "StateBucketArn",
            value=state_bucket.bucket_arn,
            export_name=self.stack_name + "-StateBucketArn",
        )
