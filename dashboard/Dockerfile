#FROM nginx
#
#COPY talent-nginx.conf /etc/nginx/nginx.conf
#COPY build /usr/share/nginx/html
#
#EXPOSE 80
#
#


#FROM gettalent/base-service-container:latest
#
## Add auth service stuff
#WORKDIR /root/base_service_container
#ADD . frontend_service
#
## Use appropriate tag name according to flask app
## RUN sed -i -e 's/TAG/FrontendService/g' /etc/syslog-ng/syslog-ng.conf
#
## Replace FLASK_APP_NAME with app nme in newrelic.ini
## RUN sed -i -e 's/FLASK_APP_NAME/FrontendService/g' newrelic.ini
#
#ADD talent-nginx.conf /etc/nginx/conf.d/
#
#EXPOSE 80
#
#CMD /etc/init.d/nginx restart

#CMD\
#    /etc/init.d/nginx restart

#    /etc/init.d/syslog-ng restart

#    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

#    newrelic-admin run-program uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --ini ./talent-uwsgi.ini





FROM node:4-onbuild

WORKDIR /
ADD . frontend_service

RUN gem update --system
RUN gem install sass
RUN gem install scss-lint
RUN gem install compass --pre
RUN gem install --pre sass-css-importer

RUN npm install
RUN npm install -g node-inspector bower gulp
RUN bower install
RUN GT_NODE_ENV=development gulp config

EXPOSE 3000

CMD GT_NODE_ENV=development gulp serve-dev