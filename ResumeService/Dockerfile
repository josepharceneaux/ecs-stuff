############################################################
# Dockerfile to build GetTalent Resume Parsing Flask Service
############################################################

# Set the base image to Ubuntu
from ubuntu:14.04
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# File Author / Maintainer
MAINTAINER Maintaner efarmer

run apt-get update

# Install basic applications
RUN apt-get install -y curl git nano wget build-essential libssl-dev gcc make zlib1g-dev libbz2-dev libreadline-dev libxml2-dev libxslt-dev

# Install Python and Basic Python Tools
RUN apt-get install -y python python-dev python-distribute python-pip python-setuptools

# Install Nginx
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository -y ppa:nginx/stable
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y nginx

# Install python pyenv
RUN curl -L https://raw.github.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

# Install Python
RUN pyenv install 2.7.9
RUN pyenv global 2.7.9

# Install UWSGI
RUN pip install uwsgi==2.0.11.1

ADD . /root/talent-resume-service/ResumeParser/
RUN rm -f /root/talent-resume-service/ResumeParser/.python-version

# Install Requirements
RUN pip install -r /root/talent-resume-service/ResumeParser/requirements.txt

# Configure Nginx
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /root/talent-resume-service/ResumeParser/talent-nginx.conf /etc/nginx/conf.d/
# RUN mkdir /etc/nginx/ssl

# Expose ports
EXPOSE 80
EXPOSE 443

# Set the default directory where CMD will execute
WORKDIR /root/talent-resume-service/ResumeParser/

# Set the default command to execute
CMD\
    eval "$(pyenv init -)" && \
    /etc/init.d/nginx restart && \
    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --ini talent-uwsgi.ini