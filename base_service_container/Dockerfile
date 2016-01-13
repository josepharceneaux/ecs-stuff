# Set the base image to Ubuntu
FROM ubuntu:14.04
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

MAINTAINER Osman Masood <osman@gettalent.com>

WORKDIR /root
ADD . base_service_container

# Update software resources repository
RUN apt-get update

# Install basic applications & Python stuff
RUN apt-get install -y curl git nano wget build-essential libssl-dev gcc make zlib1g-dev libxml2-dev libxslt1-dev libbz2-dev libreadline-dev libsqlite3-dev libmysqlclient-dev \
                       python python-dev python-distribute python-pip python-setuptools

# Install Nginx
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository -y ppa:nginx/stable
RUN apt-get update
RUN apt-get install -y nginx

# Install syslog-ng
RUN apt-get -y install rsyslog

# Uncomment UDP related variables
RUN sed -i '/$UDPServerRun/s/^#//g' /etc/rsyslog.conf
RUN sed -i '/$ModLoad imudp/s/^#//g' /etc/rsyslog.conf

RUN touch /etc/rsyslog.d/22-loggly.conf
ADD python_loggly.conf /etc/rsyslog.d/22-loggly.conf

RUN touch /etc/rsyslog.d/21-nginx-loggly.conf
ADD nginx_loggly.conf /etc/rsyslog.d/21-nginx-loggly.conf


# Install python pyenv and 2.7.9
RUN curl -L https://raw.github.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
RUN pyenv install 2.7.9
RUN pyenv global 2.7.9
CMD eval "$(pyenv init -)"
CMD ["pyenv", "shell", "2.7.9"]
CMD ["pyenv", "local", "2.7.9"]

# Install Python requirements common to all services
RUN pip install -r /root/base_service_container/requirements.txt

## Install nginx stuff
RUN rm /etc/nginx/sites-enabled/default
ADD talent-nginx.conf /etc/nginx/conf.d/

# ADD DigiCertCA.crt /usr/local/etc/ssl/DigiCertCA.crt
# ADD star_gettalent_com.crt /usr/local/etc/ssl/star_gettalent_com.crt
# ADD star_gettalent_com.key /usr/local/etc/ssl/star_gettalent_com.key
# ADD DigiCertCA.crt /etc/nginx/ssl/DigiCertCA.crt
# ADD star_gettalent_com.crt /etc/nginx/ssl/star_gettalent_com.crt
# ADD star_gettalent_com.key /etc/nginx/ssl/star_gettalent_com.key

WORKDIR /root/base_service_container
