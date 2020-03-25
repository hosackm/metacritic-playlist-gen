# Metafy Build Image

Using the AWS Lambda runtime has it's share of headaches.  In order for your application to run smoothly it must be package with all its dependencies at the same level as the main application.  When you do this packaging on your machine it's possible some dependencies will differ or be missing.  This Docker image is used to build the project in a way that AWS Lambda Python 3.7 runtime will understand.
