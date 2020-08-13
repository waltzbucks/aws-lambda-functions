# CloudFront geolication headers
https://aws.amazon.com/about-aws/whats-new/2020/07/cloudfront-geolocation-headers/

2020년 7월 24일 AWS News 에 개제된 gelolcation headers 가  추가되어 Edge location 에서 별도의 geodb 필요 없이 Viewer's header 의 Country, City 등의 정보를 이용한 Origin 을 분기 처리가 가능해 졌습니다.

이 문서는 해당 헤더를 이용하여, 특정국가에서의 요청시 CloudFront Behavior 에 지정된 Origin 이 아닌 다른 Origin 으로 요청이 전달 되도록 구현 테스트 입니다.

- [https://docs.aws.amazon.com/ko_kr/AmazonCloudFront/latest/DeveloperGuide/using-cloudfront-headers.html#cloudfront-headers-viewer-location](https://docs.aws.amazon.com/ko_kr/AmazonCloudFront/latest/DeveloperGuide/using-cloudfront-headers.html#cloudfront-headers-viewer-location)

## Architecture
- Origin request 시 CloudFront-Viewer-Country header 의 value 를 이용
- header value 가 KR 이 아닌 경우 us-east-1 EC2 Instance 를 Origin 으로 변경
- header value 가 KR 인 경우 pass (Default origin)
