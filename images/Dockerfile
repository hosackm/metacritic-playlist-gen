FROM amazonlinux:2.0.20200207.1

RUN yum update -y && yum install -y python3 python3-devel gcc gcc-c++ make && python3 -m pip install virtualenv

WORKDIR /

COPY entrypoint.sh entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
