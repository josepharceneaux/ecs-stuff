FROM gettalent/base-service-container:latest
MAINTAINER Erik Farmer <erik@gettalent.com>

WORKDIR /root/base_service_container
ADD . resume_service
WORKDIR /root/base_service_container/resume_service

EXPOSE 80
EXPOSE 443

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

CMD\
    eval "$(pyenv init -)" && \

    /etc/init.d/nginx restart && \

    export PYTHONPATH=../ && \

    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini ./talent-uwsgi.ini