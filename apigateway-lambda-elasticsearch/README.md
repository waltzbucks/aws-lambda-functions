# Lambda function: Elasticsearch service data query via API Gateway service

AWS API Gateway 서비스를 통해서 Elasticsearch service query 를 전달 하는 샘플 코드 입니다.


![image](https://user-images.githubusercontent.com/47586500/120410034-2f854400-c38d-11eb-96d6-d0841529b968.png)

# Getting start
## Requirements
* git 이 필요 합니다.
* Python 3.8 기준 으로 작성 되었습니다.
* pip3(package installer for Python3) 가 필요 합니다.
* Python reference module elasticsearch 와 aws_requests_auth 가 필요합니다.

##  Repository download
* code download

        git clone --depth 1 --filter=blob:none --no-checkout https://github.com/waltzbucks/aws-lambda-functions
        cd aws-lambda-functions/
        git checkout master -- apigateway-lambda-elasticsearch



## Code packaging
1. build.sh 를 사용하여 python virtual environment 를 setup 합니다.

        sh ./build.sh -s

2. _venv directory 가 생성 되었으면, 아래 명령으로 package zip 파일을 만듭니다.

        sh ./build.sh -b

3. 생성된 zip 파일을 Lambdb function code 에 업로드하여 사용 할 수 있습니다.
<br>e.g lambda-image-convert-1614911870.zip
