FROM gettalent/base-service-container:latest

# Add activity_service stuff
WORKDIR /root/base_service_container
ADD . activity_service

# Use appropriate tag name according to flask app
RUN sed -i -e 's/TAG/ActivityService/g' /etc/rsyslog.d/*loggly.conf

WORKDIR /root/base_service_container/activity_service

# Replace FLASK_APP_NAME with ActivityService in newrelic.ini
RUN sed -i -e 's/FLASK_APP_NAME/ActivityService/g' newrelic.ini

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

    sed -i -e "s/APP_NAME/activity_service_${GT_ENVIRONMENT}/g" /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/nginx restart && \

    /etc/init.d/rsyslog start && \

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    newrelic-admin run-program uwsgi --ini ./talent-uwsgi.ini