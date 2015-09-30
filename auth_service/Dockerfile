############################################################
# Dockerfile to build GetTalent Oauth2.0 Flask Service
############################################################

# Set the base image to Ubuntu
from ubuntu:14.04
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# File Author / Maintainer
MAINTAINER Maintaner ufarooqi

# Add the application resources URL
RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main" >> /etc/apt/sources.list
RUN apt-get update

# Install basic applications
RUN apt-get install -y curl git nano wget build-essential libssl-dev gcc make zlib1g-dev python-lxml libbz2-dev libreadline-dev libsqlite3-dev

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

# Install MySQL
RUN apt-get install -y mysql-server libmysqlclient-dev

# Copy source code to Dock Container
RUN mkdir /root/talent-flask-services

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Configure Nginx
RUN rm /etc/nginx/sites-enabled/default
RUN mkdir /etc/nginx/ssl

# Expose ports
EXPOSE 80
EXPOSE 443

# Set the default directory where CMD will execute
WORKDIR /root/talent-flask-services

# Set the default command to execute
CMD\
    eval "$(pyenv init -)" && \
    ln -s /root/talent-flask-services/auth_service/talent-nginx.conf /etc/nginx/conf.d/ && \
    pip install -r /root/talent-flask-services/requirements.txt && \
    /etc/init.d/nginx restart && \
    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini auth_service/talent-uwsgi.ini
