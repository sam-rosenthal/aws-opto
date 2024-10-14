from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as _s3,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as _apigw,
    aws_ecr_assets as _assets,
    aws_events as _events, 
    aws_events_targets as _targets,
    aws_iam as _iam,
    Duration
    # aws_sqs as sqs,
)
import os

from constructs import Construct

class SamDfsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        sportsbookOddsBucket = _s3.Bucket(self, "SportsbookOdds", bucket_name = "sportsbook-odds",
            versioned=True, removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True, cors=[_s3.CorsRule(
                allowed_methods=[
                    _s3.HttpMethods.GET, 
                    _s3.HttpMethods.PUT, 
                    _s3.HttpMethods.POST, 
                    _s3.HttpMethods.DELETE
                ],
                allowed_origins=["*"],  
                allowed_headers=["*"], 
            )])
        
        asset = _assets.DockerImageAsset(self, "MyBuildImage",
            directory=os.path.join(os.getcwd() , "lambda")
        )        
        
        my_lambda = _lambda.DockerImageFunction(self, 'ContestStructureScraper',
            code=_lambda.DockerImageCode.from_image_asset('lambda/',
                                                          cmd = ["GetContestStructure.handler"]),
            timeout=Duration.seconds(30), memory_size=512,
        )
        
        slateNamesLambda = _lambda.DockerImageFunction(self, 'GetSlateNames',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetSlateNames.handler"]),
            timeout=Duration.seconds(30), memory_size=512,
        )
        
        # slateCSVLambda = _lambda.DockerImageFunction(self, 'GetSlateCSV',
        #     code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetSlateCSV.handler"]),
        #     timeout=Duration.seconds(30), memory_size=1028,
        # )
        
        slateLambda = _lambda.DockerImageFunction(self, 'GetSlate',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetSlate.handler"]),
            timeout=Duration.seconds(30), memory_size=512,
        )
        
        bucketEnvVariables = {"BUCKET_NAME": sportsbookOddsBucket.bucket_name}
        saveEventOddsLambda = _lambda.DockerImageFunction(self, 'SaveOdds',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SaveOdds.handler"]),
            timeout=Duration.seconds(30), memory_size=512,
            environment=bucketEnvVariables
        )
        savePinnacleOddsLambda = _lambda.DockerImageFunction(self, 'SavePinnacleOddsLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SavePinnacleOdds.handler"]),
            timeout=Duration.seconds(360), memory_size=512,
            environment=bucketEnvVariables,
        )
        saveDraftkingsOddsLambda = _lambda.DockerImageFunction(self, 'SaveDraftkingsOddsLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SaveDraftkingsOdds.handler"]),
            timeout=Duration.seconds(360), memory_size=512,
            environment=bucketEnvVariables,
        )
        saveEspnOddsLambda = _lambda.DockerImageFunction(self, 'SaveEspnOddsLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SaveEspnOdds.handler"]),
            timeout=Duration.seconds(360), memory_size=512,
            environment=bucketEnvVariables,
        )
        saveFanduelOddsLambda = _lambda.DockerImageFunction(self, 'SaveFanduelOddsLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SaveFanduelOdds.handler"]),
            timeout=Duration.seconds(360), memory_size=1028,
            environment=bucketEnvVariables,
        )
        getEvLambda = _lambda.DockerImageFunction(self, 'GetEVLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetEV.handler"]),
            timeout=Duration.seconds(360), memory_size=1028,
            environment=bucketEnvVariables,
        ) 
        getPlusEvPlaysLambda = _lambda.DockerImageFunction(self, 'GetPlusEvPlaysLambda',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetPlusEvPlays.handler"]),
            timeout=Duration.seconds(60), memory_size=512,
            environment=bucketEnvVariables,
        ) 
        getLatestSavedOddsLambda = _lambda.DockerImageFunction(self, 'GetLatestSavedOdds',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["GetLatestSavedOdds.handler"]),
            timeout=Duration.seconds(60), memory_size=512,
            environment=bucketEnvVariables,
        ) 

        invokerLambda = _lambda.DockerImageFunction(self, 'SaveOddsInvoker',
            code=_lambda.DockerImageCode.from_image_asset('lambda/', cmd = ["SaveOddsInvoker.handler"]),
            timeout=Duration.seconds(360), memory_size=256,
            environment= {
                "PINNACLE": savePinnacleOddsLambda.function_arn,
                "FANDUEL": saveFanduelOddsLambda.function_arn,
                "DRAFTKINGS": saveDraftkingsOddsLambda.function_arn,
                "ESPN": saveEspnOddsLambda.function_arn},
        )
        invokerLambdaRole = invokerLambda.role
        saveOddsFunctionNames = [
            savePinnacleOddsLambda.function_name,   
            saveFanduelOddsLambda.function_name,
            saveDraftkingsOddsLambda.function_name,
            saveEspnOddsLambda.function_name,
        ]
        for functionName in saveOddsFunctionNames:
            invokerLambdaRole.add_to_policy(_iam.PolicyStatement(
                actions=['lambda:InvokeFunction'],
                resources=[f'arn:aws:lambda:us-east-1:077351908242:function:{functionName}'],
            ))

        for oddsLambda in [saveEventOddsLambda, savePinnacleOddsLambda, saveDraftkingsOddsLambda, 
                           saveEspnOddsLambda, saveFanduelOddsLambda, getEvLambda, getPlusEvPlaysLambda,
                           getLatestSavedOddsLambda]:
            sportsbookOddsBucket.grant_read_write(oddsLambda)
        
        api = _apigw.RestApi(
            self, 'MyApi',
            rest_api_name='MyApi',
            description='My API for Lambda function',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_origins=_apigw.Cors.ALL_ORIGINS,
                allow_methods=_apigw.Cors.ALL_METHODS)
            )
        
        resource = api.root.add_resource('contest-structure')
        resource.add_method('POST', _apigw.LambdaIntegration(my_lambda))
        resource = api.root.add_resource('dfs-slate')
        resource.add_method('POST', _apigw.LambdaIntegration(slateLambda))
        resource = api.root.add_resource('dfs-slate-names')
        resource.add_method('POST', _apigw.LambdaIntegration(slateNamesLambda))
        # resource = api.root.add_resource('dfs-slate-csv')
        # resource.add_method('POST', _apigw.LambdaIntegration(slateCSVLambda))
        resource = api.root.add_resource('ev')
        resource.add_method('POST', _apigw.LambdaIntegration(getEvLambda))
        resource = api.root.add_resource('plus-ev')
        resource.add_method('POST', _apigw.LambdaIntegration(getPlusEvPlaysLambda))
        resource = api.root.add_resource('latest-bets')
        resource.add_method('POST', _apigw.LambdaIntegration(getLatestSavedOddsLambda))
        # resource = api.root.add_resource('sportsbook-events')
        # resource.add_method('POST', _apigw.LambdaIntegration(sportsbookEventsLambda))
        # resource = api.root.add_resource('sportsbook-events-list')
        # resource.add_method('POST', _apigw.LambdaIntegration(sportsbookEventsListLambda))
        # resource = api.root.add_resource('sportsbook-event-odds')
        # resource.add_method('POST', _apigw.LambdaIntegration(sportsbookEventOddsLambda))

        start = 55
        for sport in ["NBA","NFL","NHL","NCAAB"]:
            rule = _events.Rule(self, f'{sport}HourlyRule', schedule=_events.Schedule.cron(minute=str(start)))
            for sportsbook in ["Pinnacle","Draftkings","Espn","Fanduel"]:
                rule.add_target(_targets.LambdaFunction(
                    invokerLambda,
                    event=_events.RuleTargetInput.from_object({"Sports": [sport], "Sportsbooks": [sportsbook]})))
            start += 1
            
        start = 29
        for sport in ["WTA","ATP"]:
            rule = _events.Rule(self, f'{sport}HourlyRule', schedule=_events.Schedule.cron(minute=str(start)))
            for sportsbook in ["Pinnacle", "Espn"]:
                rule.add_target(_targets.LambdaFunction(
                    invokerLambda,
                    event=_events.RuleTargetInput.from_object({"Sports": [sport], "Sportsbooks": [sportsbook]})))
            start += 1