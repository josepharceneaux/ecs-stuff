FROM ansible/ubuntu14.04-ansible:stable
MAINTAINER Erik Farmer <erik@gettalent.com>

WORKDIR /root
ADD web-app ResumeParser

ADD ansible/container-bootstrap.yml /srv/ansible/container-bootstrap.yml
WORKDIR /srv/ansible
RUN ansible-playbook container-bootstrap.yml -c local

RUN rm /etc/nginx/sites-enabled/default
ADD talent-nginx.conf /etc/nginx/conf.d/

WORKDIR /root/ResumeParser
EXPOSE 80

CMD\
    /etc/init.d/nginx restart && \
    uwsgi --ini ./talent-uwsgi.ini