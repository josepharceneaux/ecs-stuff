##### IMPORTANT #####
# Build this file ONLY with container_bootstrap.py! Otherwise it won't work, because the server SSL keys are encrypted
# with ansible-vault.

FROM ansible/ubuntu14.04-ansible:stable
MAINTAINER Osman Masood <osman@gettalent.com>

WORKDIR /root
ADD . talent_service

ADD ansible/container-bootstrap.yml /srv/ansible/container-bootstrap.yml
WORKDIR /srv/ansible
RUN ansible-playbook -v container-bootstrap.yml -c local

RUN rm /etc/nginx/sites-enabled/default
ADD talent-nginx.conf /etc/nginx/conf.d/
ADD DigiCertCA.crt /usr/local/etc/ssl/DigiCertCA.crt
ADD star_gettalent_com.crt /usr/local/etc/ssl/star_gettalent_com.crt
ADD star_gettalent_com.key /usr/local/etc/ssl/star_gettalent_com.key

WORKDIR /root/talent_service
# EXPOSE 80
