# CloudFront geolication headers
https://aws.amazon.com/about-aws/whats-new/2020/07/cloudfront-geolocation-headers/

2020년 7월 24일 AWS News 에 개제된 gelolcation headers 가  추가되어 Edge location 에서 별도의 geodb 필요 없이 Viewer's header 의 Country, City 등의 정보를 이용한 Origin 을 분기 처리가 가능해 졌습니다.

이 문서는 해당 헤더를 이용하여, 특정국가에서의 요청시 CloudFront Behavior 에 지정된 Origin 이 아닌 다른 Origin 으로 요청이 전달 되도록 구현 테스트 입니다.

- [https://docs.aws.amazon.com/ko_kr/AmazonCloudFront/latest/DeveloperGuide/using-cloudfront-headers.html#cloudfront-headers-viewer-location](https://docs.aws.amazon.com/ko_kr/AmazonCloudFront/latest/DeveloperGuide/using-cloudfront-headers.html#cloudfront-headers-viewer-location)

## Architecture
- Origin request 시 CloudFront-Viewer-Country header 의 value 를 이용
- header value 가 KR 이 아닌 경우 us-east-1 EC2 Instance 를 Origin 으로 변경
- header value 가 KR 인 경우 pass (Default origin)
---

## Step 1. EC2 Instance 준비

이 문서에서는 EC2 Instance 구성 방법은 생략 합니다.

1. Virginia 와 Seoul region 에 각각 Web service EC2  Instance 를 Public network 로 구성 하여 Public DNS 정보를 복사합니다.
2. Seoul region 의 EC2 Instance Public DNS 를 CloudFront distribution 의 Origin 으로 설정 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/5da8907d-00b0-4718-a89b-e4efa26addc3/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/5da8907d-00b0-4718-a89b-e4efa26addc3/Untitled.png)

## Step 2. IAM Role 생성

Lambda function 실행을 위한 IAM Role 을 생성 합니다.

1. [IAM Management Console](https://console.aws.amazon.com/iam/) 에서 **Create role** 을 선택 합니다.
2. Choose use case 에서 **Lambda** 를 선택 합니다.
3. Attach permissions policies 에서 아래 Role 을 선택 합니다.

    ```
    AmazonS3FullAccess
    AWSLambdaBasicExecutionRole
    ```

4. Next: tag, Next: review 를 선택합니다.
5. Role name AWSLambdaEdgeRole 을 입력하고 Create role 을 선택 합니다.
6. 생성된 Role 에 Add inline policy 로 아래 설정을 추가 합니다.

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "iam:CreateServiceLinkedRole",
                    "lambda:GetFunction",
                    "cloudfront:UpdateDistribution",
                    "cloudfront:CreateDistribution",
                    "lambda:EnableReplication"
                ],
                "Resource": "*"
            }
        ]
    }
    ```
7. Policy name 은 AWSLambdaEdgePolicy 를 입력 한뒤 Create policy 를 선택 합니다.
8. 생성한 IAM Role AWSLambdaEdgeRole 에서 Trust relationships 탭에 edit trust relationship 버튼을 선택 후 아래 내용으로 업데이트 합니다.

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": [
              "lambda.amazonaws.com",
              "edgelambda.amazonaws.com"
            ]
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

## Step 3. Lambda function 생성

해당 Lambda code 는 python3 로 작성 하였습니다.

### Step 3.1. Lambda function create

1. AWS Management console 에서 Region 을 **US East (N. Virginia) us-east-1** 로 변경 합니다.
2. [Lambda function console](https://console.aws.amazon.com/lambda/) 에서 Create function 을 선택 합니다.
3. Basic information 설정
    - Function name = ViewerGeoTurnOrigin
    - Runtime = Python 3.8
    - Use an existing role = AWSLamgdaEdgeRole

        ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/09477aee-48b8-4b68-824d-a94f9881d571/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/09477aee-48b8-4b68-824d-a94f9881d571/Untitled.png)

4. Create function 선택 합니다.

### Step 3.2. Lambda function code 작성

Lambda management console 에서  생성한 ViewerGeoTurnOrigin function 에 **lambda_function.py** 로 저장 또는 업로드 합니다.

- 24번 라인의 **"domainName"** 을 Step 1에서 생성한 Virginia EC2 Instance 의 Public DNS 로 변경 해야 합니다.

    ```python
    #!/usr/bin/env python

    import logging

    logging.getLogger().setLevel(logging.INFO)

    def lambda_handler(event, context):
        
        logging.info('event::{}'.format(event))

        try:
            request_dict = event.get('Records')[0].get('cf').get('request')
            request_headers = request_dict.get('headers')
            req_host = request_headers.get('host')[0]['value']
            
            if request_headers['cloudfront-viewer-country'][0]['value'] != 'KR':
                
                logging.info('Cloudfront-Viewer-Country: ' + str(request_headers['cloudfront-viewer-country'][0]['value']))
                logging.info(request_dict.get('uri'))
                
                custom_origin = {
                    "custom": {
                        "customHeaders": {},
                        "domainName": "ec2-54-87-200-95.compute-1.amazonaws.com",   # AWS Virginia EC2 Instance
                        "keepaliveTimeout": 5,
                        "path": "",
                        "port": 80,
                        "protocol": "http",
                        "readTimeout": 30,
                        "sslProtocols": [
                            "TLSv1",
                            "TLSv1.1",
                            "TLSv1.2"
                        ]
                    }
                }
                
                logging.info('custom_origin::{}'.format(custom_origin))
                
                request_dict['origin'] = custom_origin
                request_dict['headers']['host'] = [{
                    'key': 'Host',
                    'value': 'www.example.com'
                }]
                
                logging.info('custom_origin::{}'.format(request_dict))
                
            return request_dict
                

        except Exception as e:
            logging.error('exception::{1}'.format(e.args[0], e))

            return {
                'status': 500,
                'statusDescription': 'Internal server error',
            }

        logging.info('request_dict::{}'.format(request_dict))
    ```

### Step 3.3. Lambda Publish new version

CloudFront 에 Lambda function 을 배포하기위해 Version 을 생성 해야 합니다.

1. Lambda function management console 에서 Actions 버튼을 눌러 **Publish new version** 메뉴를 선택하고, 팝업 화면에서 Publish 를 선택 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/4ad249ff-6e5a-4632-bf91-07c5f499cdaf/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/4ad249ff-6e5a-4632-bf91-07c5f499cdaf/Untitled.png)

2. 새로 생성된 버전의 ARN 을 복사 합니다.

## Step 4. CloudFront Behavior Setting

### Step 4.1. Origin request policy 생성

CloudFront viewer geolocation headers 를 사용하기위해 Origin Request Policy 를 생성 해야 합니다.

1. [CloudFront management console](https://console.aws.amazon.com/cloudfront/) 에서 Policies 을 선택 합니다.
2. **Origin request policy** 탭에서 ****Create origin request policy 를 선택 합니다.
3. Info > Name 과 Comment 에 AllViewerHeaders 를 입력 합니다.
4. Origin request contents > Headers 에 리스트 목록에서 **All viewer headers and whitelisted CloudFront-* headers** 를 선택 하고,
*Choose from the list* 에서 CloudFront-Viewer-Country 검색하여 Add header 버튼을 선택 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/aee77239-a4c7-4c6b-8ac1-948e207f3ffd/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/aee77239-a4c7-4c6b-8ac1-948e207f3ffd/Untitled.png)

5. Create origin request policy 버튼을 선택 합니다.

### Step 4.2. Distribution setting

1. [CloudFront management console](https://console.aws.amazon.com/cloudfront/) 에서 서비스 Distribution 을 선택 합니다.
2. Behaviors 탭을 선택. Lambda function 을 적용 하기위한 Behavior 를 Edit 합니다.
3. **Cache and origin request settings** 에서 Use a cache policy and origin request policy 로 선택 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/dcba5ac8-1fc2-46da-ad2c-3341eca850fd/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/dcba5ac8-1fc2-46da-ad2c-3341eca850fd/Untitled.png)

4. 활성화 된 옵션 메뉴를 아래와 같이 선택 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/356dcf74-533d-4f32-bcc3-9fc5efe54d8c/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/356dcf74-533d-4f32-bcc3-9fc5efe54d8c/Untitled.png)

    - Cache Policy = Managed-CachingDisabled
    - Origin Request Policy = AllViewerHeaders

5. 가장 아래 Lambda Function Associations 을 설정 합니다.

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/27519e11-5111-4e1c-a0d8-cc8a9307221b/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/27519e11-5111-4e1c-a0d8-cc8a9307221b/Untitled.png)

    - CloudFront Event = Origin Request
    - Lambda Function ARN = *위에서 Publish한 버전의 ARN*

6. Yes, Edit 선택하여 배포 합니다.

## Step 5. Test

각 Region 의 EC2 Instance web-server 에 구분 할수 있는 contents 를 생성하여 CloudFront 로 확인 해봅니다.

- 국내(KR) 에서 요청시

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/7a282904-2996-4b21-a1a1-3c2a780285c8/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/7a282904-2996-4b21-a1a1-3c2a780285c8/Untitled.png)

- 해외에서 요청시

    ![https://s3-us-west-2.amazonaws.com/secure.notion-static.com/9ae15c0c-7cd4-4e7c-b3ec-a08335381734/Untitled.png](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/9ae15c0c-7cd4-4e7c-b3ec-a08335381734/Untitled.png)

## Step 6. Resource 삭제

### Step 6.1. CloudFront Associate lambda function

1. CloudFront behavior 에서 Lambda Function Associations 항목을 제거 합니다.

### Step 6.2. Lambda function delete

1. US East (N. Virginia) us-east-1 Region 에 등록되어 있는 Lambda function 을 삭제 합니다.

### Setp 6.3. EC2 Instance delete

1. Virginia 와 Seoul region 의 EC2 Instance 를 termination 합니다.

---
