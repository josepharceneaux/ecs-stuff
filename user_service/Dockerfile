FROM gettalent/base-service-container:latest

# Add files
WORKDIR /root/base_service_container
ADD . user_service
WORKDIR /root/base_service_container/user_service

# Replace app name in config Loggly and NewRelic config files
RUN sed -i -e 's/APP_NAME/user_service/g' newrelic.ini /etc/rsyslog.d/*loggly.conf

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

    sed -i -e 's/GT_ENVIRONMENT/$GT_ENVIRONMENT/g' /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/rsyslog start && \

    /etc/init.d/nginx restart && \

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    newrelic-admin run-program uwsgi --ini ./talent-uwsgi.ini