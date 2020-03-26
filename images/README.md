# Metafy Build Image

Using the AWS Lambda runtime has it's share of headaches.  In order for your application to run smoothly it must be package with all its dependencies at the same level as the main application.  When you do this packaging on your machine it's possible some dependencies will differ or be missing.  This Docker image is used to build the project in a way that AWS Lambda Python 3.7 runtime will understand.

## To build
In order to build this image run the following command from within the images/ directory:

    docker build . -t metafy

## To run

Running this image will create a zip package for deployment in S3.  To do this run:

    docker run -v $(pwd):/outputs metafy
