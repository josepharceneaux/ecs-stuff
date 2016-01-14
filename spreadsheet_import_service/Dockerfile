FROM gettalent/base-service-container:latest

<<<<<<< HEAD
# Add spreadsheet_import_service stuff
WORKDIR /root/base_service_container
ADD . spreadsheet_import_service

# Use appropriate tag name according to flask app
RUN sed -i -e 's/TAG/SpreadsheetImportService/g' /etc/rsyslog.d/*loggly.conf

WORKDIR /root/base_service_container/spreadsheet_import_service

# Replace FLASK_APP_NAME with SpreadsheetImportService in newrelic.ini
RUN sed -i -e 's/FLASK_APP_NAME/SpreadsheetImportService/g' newrelic.ini
=======
# Add files
WORKDIR /root/base_service_container
ADD . spreadsheet_import_service
WORKDIR /root/base_service_container/spreadsheet_import_service

# Replace app name in config Loggly and NewRelic config files
RUN sed -i -e 's/APP_NAME/spreadsheet_import_service/g' newrelic.ini /etc/rsyslog.d/*loggly.conf
>>>>>>> 0c10eb24619f68e7c70cd04e33b20d474a79867e

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

<<<<<<< HEAD
    sed -i -e "s/APP_NAME/spreadsheet_import_service_${GT_ENVIRONMENT}/g" /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/nginx restart && \

    /etc/init.d/rsyslog start && \
=======
    sed -i -e 's/GT_ENVIRONMENT/$GT_ENVIRONMENT/g' /etc/rsyslog.d/*loggly.conf && \

    /etc/init.d/rsyslog start && \

    /etc/init.d/nginx restart && \
>>>>>>> 0c10eb24619f68e7c70cd04e33b20d474a79867e

    export NEW_RELIC_ENVIRONMENT=$GT_ENVIRONMENT && export NEW_RELIC_CONFIG_FILE=newrelic.ini && \

    newrelic-admin run-program uwsgi --ini ./talent-uwsgi.ini