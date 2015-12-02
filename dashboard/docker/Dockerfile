FROM ubuntu:14.04
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

MAINTAINER Jordan Seaberg <jordan@gettalent.com>

WORKDIR /root
RUN mkdir dashboard
COPY .. dashboard

# Install Nginx
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:nginx/stable
RUN apt-get update && apt-get install -y nginx

# Install Nginx stuff
RUN rm /etc/nginx/sites-enabled/default
COPY talent-nginx.conf /etc/nginx/conf.d/

# Turn off nginx starting as a daemon
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Purge APT cache
RUN apt-get clean all

EXPOSE 80 443
CMD ["/etc/init.d/nginx", "restart"]

WORKDIR /root/dashboard
