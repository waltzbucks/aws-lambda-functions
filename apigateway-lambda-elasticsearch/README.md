
# Lambda function: Elasticsearch service data query via API Gateway service

AWS API Gateway 서비스를 통해서 Elasticsearch service query 를 전달 하는 샘플 코드 입니다.


![image](https://user-images.githubusercontent.com/47586500/120410034-2f854400-c38d-11eb-96d6-d0841529b968.png)

- [Lambda function: Elasticsearch service data query via API Gateway service](#lambda-function-elasticsearch-service-data-query-via-api-gateway-service)
- [Prerequisite](#prerequisite)
- [Getting start](#getting-start)
  - [1. Repository download](#1-repository-download)
  - [2. IAM Role & STS Assume role](#2-iam-role--sts-assume-role)
    - [2.1. IAM Role create](#21-iam-role-create)
    - [2.2. AWS Security Token Service(STS) Assume role config](#22-aws-security-token-servicests-assume-role-config)
    - [2.3. IAM Role permissions attach](#23-iam-role-permissions-attach)
  - [3. Amazon Elasticsearch service](#3-amazon-elasticsearch-service)
    - [3.1.  Prerequisite](#31--prerequisite)
    - [3.2. Create an Elasticsearch domain](#32-create-an-elasticsearch-domain)
    - [3.3. Insert sample data](#33-insert-sample-data)
    - [3.4. Roles mapping](#34-roles-mapping)
  - [4. Lambda function](#4-lambda-function)
    - [4.1. Build](#41-build)
    - [4.2. Lambda function create](#42-lambda-function-create)
  - [5. API Gateway](#5-api-gateway)
    - [5.1.  REST API 를 생성](#51--rest-api-를-생성)
    - [5.2. Resource "/type" 생성](#52-resource-type-생성)
    - [5.3. "GET" Method 생성](#53-get-method-생성)
    - [5.4. Lambda permission 추가 (event trigger)](#54-lambda-permission-추가-event-trigger)
    - [5.5. Deployment](#55-deployment)
    - [5.6. Test](#56-test)
  - [6. API-Key 사용](#6-api-key-사용)
    - [6.1. API-Key 생성](#61-api-key-생성)
    - [6.2. Usage plans 설정](#62-usage-plans-설정)
    - [6.3. Method 에 API Key Required 변경](#63-method-에-api-key-required-변경)
    - [6.4. Deployment](#64-deployment)
    - [6.5. Test](#65-test)


# Prerequisite
원할한 진행을 위해 다음과 같은 도구들이 필요로 합니다.
- AWS CLI Install

    Guide Link: [https://docs.aws.amazon.com/ko_kr/cli/latest/userguide/cli-chap-install.html](https://docs.aws.amazon.com/ko_kr/cli/latest/userguide/cli-chap-install.html)

- Python3

    Guide Link: [https://realpython.com/installing-python/](https://realpython.com/installing-python/)

- PIP

    Guide Link: [https://pip.pypa.io/en/stable/installing/](https://pip.pypa.io/en/stable/installing/)

- virtualenv

    Guide Link: [https://virtualenv.pypa.io/en/latest/installation.html](https://virtualenv.pypa.io/en/latest/installation.html)

- jq

     Guide Link: [https://stedolan.github.io/jq/download/](https://stedolan.github.io/jq/download/)

- curl

    Guide Link: [https://curl.se/download.html](https://curl.se/download.html)

# Getting start

## 1. Repository download
* code download

        git clone --depth 1 --filter=blob:none --no-checkout https://github.com/waltzbucks/aws-lambda-functions
        cd aws-lambda-functions/
        git checkout master -- apigateway-lambda-elasticsearch



## 2. IAM Role & STS Assume role
Lambda function 에서 각 서비스로 접근이 필요한 권한을 위한 Role 을 설정 합니다.

### 2.1. IAM Role create

2.1.1. policy 파일을 확인 합니다.

- File: iam-role-trust-policy.json

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "",
          "Effect": "Allow",
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

2.1.2. IAM Role 을 생성 합니다.

- AWS CLI

    ```bash
    aws iam create-role --role-name lambda-es-search-role --assume-role-policy-document="$(cat iam-role-trust-policy.json | jq -c '.' )"
    ```

2.1.3. 생성된 IAM Role 의 ARN 정보를 확인 합니다.

- AWS CLI

    ```bash
    aws iam list-roles |  grep "role/lambda-es-search-role" | sed -En  "s/^.*(arn.*)\",/\1/p"
    ```

### 2.2. AWS Security Token Service(STS) Assume role config

2.2.1. 아래 policy 파일에 <IAMROLEARN> 부분을 위에서 확인한 ARN 정보로 변경한 뒤 저장 합니다.

- File: iam-role-trust-policy-mod.json

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "",
          "Effect": "Allow",
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        },
        {
          "Sid": "AllowlambdaToAssumeRole",
          "Effect": "Allow",
          "Principal": {
            "AWS": "<IAMROLEARN>"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

2.2.2. IAM Role 을 위에 생성한 policy 파일로 업데이트 합니다. 

- AWS CLI

    ```json
    aws iam update-assume-role-policy --role-name lambda-es-search-role --policy-document="$(cat iam-role-trust-policy-mod.json | jq -c '.')" 
    ```

### 2.3. IAM Role permissions attach

2.3.1. Amazon Elasticsearch service access permission policy 를 attach 합니다.

- AWS CLI

    ```bash
    aws iam attach-role-policy --role-name lambda-es-search-role  --policy-arn arn:aws:iam::aws:policy/AmazonESFullAccess
    ```

2.3.2. AWS Lambda execute permission policy 를 attach 합니다.

- AWS CLI

    ```bash
    aws iam attach-role-policy --role-name lambda-es-search-role  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    ```

3.3. Amazon CloudWatch logs permission policy 를 추가 합니다. (No need it)

- AWS CLI

    ```bash
    aws iam put-role-policy --role-name lambda-es-search-role --policy-name logs --policy-document='{"Version":"2012-10-17","Statement":[{"Sid":"","Resource":"*","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Effect":"Allow"}]}'
    ```

## 3. Amazon Elasticsearch service

해당 문서에서는 Amazon Elasticsearch service domain 으로 openapisearch 를 예제로 사용 합니다.

### 3.1.  Prerequisite

3.1.1. Amazon Elasticsearch service access policy 에 적용할 파일을 생성 합니다.

- File: es-access-policy.json

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "AWS": "*"
          },
          "Action": "es:*",
          "Resource": "arn:aws:es:ap-northeast-2:<YOURACCOUNT>:domain/openapisearch/*"
        }
      ]
    }
    ```

### 3.2. Create an Elasticsearch domain

3.2.1. Elasticsearch domain 을 생성 합니다.

- AWS CLI

    ```bash
    aws --region ap-northeast-2 es create-elasticsearch-domain \
    --domain-name openapisearch \
    --elasticsearch-version 7.10 \
    --elasticsearch-cluster-config InstanceType=r6g.large.elasticsearch,InstanceCount=1 \
    --ebs-options EBSEnabled=true,VolumeType=gp2,VolumeSize=10 \
    --access-policies file://es-access-policy.json \
    --node-to-node-encryption-options Enabled=true \
    --encryption-at-rest-options  Enabled=true \
    --domain-endpoint-options 'EnforceHTTPS=true,TLSSecurityPolicy=Policy-Min-TLS-1-2-2019-07' \
    --advanced-security-options 'Enabled=true,InternalUserDatabaseEnabled=true,MasterUserOptions={MasterUserName=handsonlab,MasterUserPassword=Goswm5!ab}'
    ```

    ⚠️ AWS CLI Command Reference: [https://docs.aws.amazon.com/cli/latest/reference/es/create-elasticsearch-domain.html](https://docs.aws.amazon.com/cli/latest/reference/es/create-elasticsearch-domain.html)

3.2.2. Elasticsearch domain 생성 진행 상태를 확인 합니다.

- AWS CLI

    ```bash
    aws es describe-elasticsearch-domain \
    --domain-name openapisearch \
    --query 'DomainStatus.Processing'
    ```

    ⚠️ Return 값이 false 인 경우 domain 생성이 완료된 상태를 의미 합니다.

3.2.3. Endpoint domain 으로 cluster 의 heath 정보를 확인 합니다.

- AWS CLI & Shell command

    ```bash
    AWS_ES_ENDPOINT=$(aws es describe-elasticsearch-domain \
    --domain-name openapisearch \
    --query 'DomainStatus.Endpoint' \
    --output text) &&
    echo $AWS_ES_ENDPOINT && 
    curl -u handsonlab:Goswm5\!ab -X GET "https://$AWS_ES_ENDPOINT/_cat/health?v&pretty" 
    ```

### 3.3. Insert sample data

3.3.1. github 에서 sample data 를 받습니다.

```bash
git clone https://github.com/CloudAffaire/sample_data.git && cd sample_data
```

3.3.2. Sample data 를 입력합니다.

```bash
curl -u handsonlab:Goswm5\!ab -XPUT "https://$AWS_ES_ENDPOINT/cloudaffairempldb?pretty" \                                                                                           
-H 'Content-Type: application/json' \
-d @Employees25KHeader.json &&
curl -u handsonlab:Goswm5\!ab -XPUT "https://$AWS_ES_ENDPOINT/cloudaffairempldb/_bulk" \
-H 'Content-Type: application/json' \
--data-binary @Employees25K.json
```

3.3.3. Indice 를 확인 합니다.

```bash
curl -u handsonlab:Goswm5\!ab -X GET "https://$AWS_ES_ENDPOINT/_cat/indices" 
```

3.3.4. _search query 결과를 확인 합니다.

```
curl -u handsonlab:Goswm5\!ab -XGET "https://$AWS_ES_ENDPOINT/cloudaffairempldb/_search" \
-H 'Content-Type: application/json' \
-d '{"query": {"match": {"_type": "employees"}}}'
```

### 3.4. Roles mapping

3.4.1. Roles mapping for Lambda function

- API Call

    ```bash
    export AWS_ES_ENDPOINT=$(aws es describe-elasticsearch-domain --domain-name openapisearch --query 'DomainStatus.Endpoint' --output text)

    export AWS_IAM_ROLE=$(aws iam list-roles |  grep "role/lambda-es-search-role" | sed -En  "s/^.*(arn.*)\",/\1/p")

    curl -u handsonlab:Goswm5\!ab -X PATCH "https://$AWS_ES_ENDPOINT/_opendistro/_security/api/rolesmapping/all_access?pretty" \
    -H 'Content-Type: application/json' \
    -d "[{\"op\": \"replace\", \"path\": \"/backend_roles\", \"value\": [\"$AWS_IAM_ROLE\"]}]"
    ```

    reference: [https://www.eksworkshop.com/intermediate/230_logging/config_es/](https://www.eksworkshop.com/intermediate/230_logging/config_es/)

## 4. Lambda function

### 4.1. Build

4.1.1. Clone

- github 에서 sample code 를 다운 받습니다.

    ```bash
    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/waltzbucks/aws-lambda-functions && cd aws-lambda-functions/ && git checkout master -- apigateway-lambda-elasticsearch
    ```

4.1.2. config file 생성 합니다.

- Shell command

    ```bash
    export AWS_ES_ENDPOINT=$(aws es describe-elasticsearch-domain --domain-name openapisearch --query 'DomainStatus.Endpoint' --output text)

    export AWS_IAM_ROLE=$(aws iam list-roles |  grep "role/lambda-es-search-role" | sed -En  "s/^.*(arn.*)\",/\1/p")

    echo "{\"es_host\": \"$AWS_ES_ENDPOINT\",\"es_region\": \"ap-northeast-2\",\"es_connection_timeout\": 60,\"es_bulk_timeout\": \"60s\",\"es_bulk_chunk_size\": 1000,\"sts_role_arn\": \"$AWS_IAM_ROLE\",\"sts_session_name\": \"lambdastsassume\"}" 2>&1 | python -m json.tool > json/es-access-config.json
    ```

4.1.3. Build

- Shell command

    ```bash
    ./build.sh -s && filename=`./build.sh -b `
    ```

### 4.2. Lambda function create

4.2.1. 위에서 빌드 된 .zip 파일과 함께 Lambda function 을 생성 합니다.

- AWS CLI

    ```bash
    export AWS_IAM_ROLE=$(aws iam list-roles |  grep "role/lambda-es-search-role" | sed -En  "s/^.*(arn.*)\",/\1/p")

    aws lambda create-function \
    --function-name openapisearch-function \
    --runtime python3.8 \
    --handler lambda_function.lambda_handler \
    --role $AWS_IAM_ROLE \
    --timeout 60 \
    --memory-size 1024 \
    --zip-file fileb://$filename
    ```

4.2.2. AWS Lambda function console 에서 Test event 를 시도 합니다.

- Test event

    ```bash
    {"queryStringParameters": {"q": "ceo"}}
    ```

## 5. API Gateway

### 5.1.  REST API 를 생성

- AWS CLI

    ```bash
    # Create API Gateway REST API
    aws apigateway create-rest-api --name searchapi \
    --api-key-source "HEADER" \
    --endpoint-configuration "types=REGIONAL"
    ```

### 5.2. Resource "/type" 생성

- AWS CLI

    ```bash
    # Create resource
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    export PARENT_ID=`aws apigateway get-resources --rest-api-id $REST_API_ID | jq -r -c '.items[] | select( .path == "/" ) | .id'`

    aws apigateway create-resource \
    --rest-api-id $REST_API_ID \
    --parent-id $PARENT_ID \
    --path-part "search"
    ```

### 5.3. "GET" Method 생성

5.3.1. "/type" Resource 에 "GET" method 를 생성 합니다. 

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    export RESOURCE_ID=`aws apigateway get-resources --rest-api-id $REST_API_ID | jq -r -c '.items[] | select( .pathPart == "search" ) | .id'`

    aws apigateway put-method \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method "GET" \
    --authorization-type "NONE"

    aws apigateway put-method-response \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method "GET" \
    --status-code "200" \
    --response-models '{"application/json": "Empty"}'
    ```

5.3.2. Integration 을 설정 합니다.

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    export RESOURCE_ID=`aws apigateway get-resources --rest-api-id $REST_API_ID | jq -r -c '.items[] | select( .pathPart == "search" ) | .id'`

    export LAMBDA_ARN=`aws lambda get-function --function-name openapisearch-function | jq -r -c '.Configuration.FunctionArn'`

    aws apigateway put-integration \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method "GET" \
    --type AWS_PROXY \
    --integration-http-method "POST" \
    --content-handling "CONVERT_TO_TEXT" \
    --uri "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"

    aws apigateway put-integration-response \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method "GET" \
    --status-code "200" \
    --response-templates '{"application/json": ""}'
    ```

5.3.3. 생성된 Method 정보를 확인 합니다.

- AWS CLI

    ```bash
    aws apigateway get-method \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method "GET"
    ```

### 5.4. Lambda permission 추가 (event trigger)

Lambda function 에 permission 을 추가 합니다.

- AWS CLI

    ```bash
    aws lambda add-permission \
    --function-name openapisearch-function \
    --statement-id apigateway-get \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:`aws configure get region`:`aws sts get-caller-identity | jq -r -c '.Account'`:`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`/*/GET/search"
    ```

    ⚠️ [https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/arn-format-reference.html](https://docs.aws.amazon.com/ko_kr/apigateway/latest/developerguide/arn-format-reference.html)

- Lambda function 에 권한을 확인 합니다.

    ```bash
    aws lambda get-policy --function-name openapisearch-function
    ```

### 5.5. Deployment

Deploy stage "prod" 로 배포 합니다

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name "prod"
    ```

    ⚠️ "prod" stage 생성과 동시에 배포 합니다.

### 5.6. Test

- AWS CLI

    ```bash
    export INVOKE_DOMAIN="`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`.execute-api.ap-northeast-2.amazonaws.com"

    curl -s https://$INVOKE_DOMAIN/prod/search\?q\=ceo  | jq
    ```

- Output

    ```json
    [
      {
        "FirstName": "ELVA",
        "LastName": "RECHKEMMER",
        "Designation": "CEO",
        "Salary": "154000",
        "DateOfJoining": "1993-01-11",
        "Address": "8417 Blue Spring St. Port Orange, FL 32127",
        "Gender": "Female",
        "Age": 62,
        "MaritalStatus": "Unmarried",
        "Interests": "Body Building,Illusion,Protesting,Taxidermy,TV watching,Cartooning,Skateboarding"
      }
    ]
    ```

## 6. API-Key 사용

X-API-Key 헤더를 이용한 인증키 사용 설정을 합니다.

### 6.1. API-Key 생성

- AWS CLI

    ```bash
    aws apigateway create-api-key \
    --name searchapi-key-1 \
    --enabled
    ```

### 6.2. Usage plans 설정

6.2.1. usage plan 생성 합니다.

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    aws apigateway create-usage-plan \
    --name "searchapikeys" \
    --api-stages "apiId"=$REST_API_ID,"stage"="prod"
    ```

6.2.2. API-Key 를 Usage plan 에 추가 합니다.

- AWS CLI

    ```bash
    export PLAN_ID=`aws apigateway get-usage-plans | jq -r -c '.items[] | select(.name == "searchapikeys") .id'`
    export APIKEY_ID=`aws apigateway get-api-keys | jq -r -c '.items[] | select(.name == "searchapi-key-1") .id'`

    aws apigateway create-usage-plan-key \
    --usage-plan-id $PLAN_ID \
    --key-id $APIKEY_ID \
    --key-type "API_KEY"
    ```

- Output

    ```bash
    {
        "id": "gl6fdtzx33",
        "type": "API_KEY",
        "value": "RfolLtE23u9Be6hDf3sf72otkAXWPxwE6aFSKgxE",
        "name": "searchapi-key-1"
    }
    ```

### 6.3. Method 에 API Key Required 변경

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    export RESOURCE_ID=`aws apigateway get-resources --rest-api-id $REST_API_ID | jq -r -c '.items[] | select( .pathPart == "search" ) | .id'`

    aws apigateway update-method \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --patch-operations op="replace",path="/apiKeyRequired",value="true"
    ```

### 6.4. Deployment

Deploy stage "prod" 로 배포 합니다

- AWS CLI

    ```bash
    export REST_API_ID=`aws apigateway get-rest-apis | jq -r -c '.items[] | select( .name == "searchapi" ) | .id'`

    aws apigateway create-deployment \
    --rest-api-id $REST_API_ID \
    --stage-name "prod"
    ```

### 6.5. Test

- AWS CLI

    ```bash
    export APIKEY_VALUE=`aws apigateway  get-api-key --api-key $APIKEY_ID --include-value | jq -r -c '.value'`

    curl -s https://$INVOKE_DOMAIN/prod/search\?q\=ceo  -H "X-API-Key: $APIKEY_VALUE" | jq
    ```

- Output

    ```json
    [
      {
        "FirstName": "ELVA",
        "LastName": "RECHKEMMER",
        "Designation": "CEO",
        "Salary": "154000",
        "DateOfJoining": "1993-01-11",
        "Address": "8417 Blue Spring St. Port Orange, FL 32127",
        "Gender": "Female",
        "Age": 62,
        "MaritalStatus": "Unmarried",
        "Interests": "Body Building,Illusion,Protesting,Taxidermy,TV watching,Cartooning,Skateboarding"
      }
    ]
    ```