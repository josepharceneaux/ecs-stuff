FROM gettalent/base-service-container:latest

# Add candidate service stuff
WORKDIR /root/base_service_container
ADD . candidate_service
WORKDIR /root/base_service_container/candidate_service

# Replace app name in config Loggly and NewRelic config files
RUN sed -i -e 's/APP_NAME/candidate_service/g' newrelic.ini /etc/rsyslog.d/*loggly.conf

EXPOSE 80

# Set PYTHON PATH
ENV PYTHONPATH ../

ENV C_FORCE_ROOT true

CMD\
    eval "$(pyenv init -)" && \

    sed -i -e "s/GT_ENVIRONMENT/$GT_ENVIRONMENT/g" /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/rsyslog start && \

    /etc/init.d/nginx restart && \

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    if [[ "${GT_ENVIRONMENT}" -eq "jenkins" ]]; then uwsgi --lazy --ini ./talent-uwsgi.ini; else newrelic-admin \
    run-program uwsgi --lazy --ini ./talent-uwsgi.ini; fi