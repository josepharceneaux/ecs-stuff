FROM gettalent/base-service-container:latest

# Install nginx stuff
ADD talent-nginx.conf /etc/nginx/conf.d/

# Add auth service stuff
WORKDIR /root/base_service_container
ADD . activity_service
WORKDIR /root/base_service_container/activity_service

EXPOSE 80

# Set DB connection string`
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

CMD\
    eval "$(pyenv init -)" && \

    /etc/init.d/nginx restart && \

    export PYTHONPATH=../ && \

    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini ./talent-uwsgi.ini