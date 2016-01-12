FROM gettalent/base-service-container:latest

# Add candidate service stuff
WORKDIR /root/base_service_container
ADD . candidate_service

# Use appropriate tag name according to flask app
RUN sed -i -e 's/TAG/CandidateService/g' /etc/rsyslog.d/*loggly.conf

WORKDIR /root/base_service_container/candidate_service

# Replace FLASK_APP_NAME with CandidateService in newrelic.ini
RUN sed -i -e 's/FLASK_APP_NAME/CandidateService/g' newrelic.ini

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

    sed -i -e "s/APP_NAME/candidate_service_${GT_ENVIRONMENT}/g" /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/nginx restart && \

    /etc/init.d/rsyslog start && \

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    newrelic-admin run-program uwsgi --ini ./talent-uwsgi.ini