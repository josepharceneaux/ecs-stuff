FROM gettalent/base-service-container:latest

# Add auth service stuff
WORKDIR /root/base_service_container
ADD . spreadsheet_import_service

# Use appropriate tag name according to flask app
RUN sed -i -e 's/TAG/SpreadsheetImportService/g' /etc/syslog-ng/syslog-ng.conf

WORKDIR /root/base_service_container/spreadsheet_import_service

# Replace FLASK_APP_NAME with AuthService in newrelic.ini
RUN sed -i -e 's/FLASK_APP_NAME/SpreadsheetImportService/g' newrelic.ini

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

    /etc/init.d/nginx restart && \

    /etc/init.d/syslog-ng restart && \

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    newrelic-admin run-program uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini ./talent-uwsgi.ini