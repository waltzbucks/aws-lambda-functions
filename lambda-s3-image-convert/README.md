# Lambda function: Image convert by was upload to S3 Bucket

S3 로 업로드 되는 이미지파일에 대해서 여러 사이즈로 변환하여 S3 Bucket 에 업로드 하는 샘플 코드 입니다.

![image](https://user-images.githubusercontent.com/47586500/110078588-4ab2d880-7dcb-11eb-855f-750e0ea3e74b.png)

# Getting start
## Requirements
* git 이 필요 합니다.
* Python 3.8 기준 으로 작성 되었습니다.
* pip3(package installer for Python3) 가 필요 합니다.
* Python reference module Pillow 가 필요합니다.

##  Repository download
* code download

        git clone --depth 1 --filter=blob:none --no-checkout https://github.com/waltzbucks/aws-lambda-functions
        cd aws-lambda-functions/
        git checkout master -- lambda-s3-image-convert



## Code packaging
1. build.sh 를 사용하여 python virtual environment 를 setup 합니다.

        sh ./build.sh -s

2. _venv directory 가 생성 되었으면, 아래 명령으로 package zip 파일을 만듭니다.

        sh ./build.sh -b

3. 생성된 zip 파일을 Lambdb function code 에 업로드하여 사용 할 수 있습니다.
<br>e.g lambda-image-convert-1614911870.zip
