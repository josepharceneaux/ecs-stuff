############################################################
# Dockerfile to build GetTalent Oauth2.0 Flask Service
############################################################

FROM gettalent/base-service-container:latest

WORKDIR /root/base_service_container
ADD . auth_service
WORKDIR /root/base_service_container/auth_service

EXPOSE 80
EXPOSE 443

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

CMD\
    eval "$(pyenv init -)" && \

    /etc/init.d/nginx restart && \

    export PYTHONPATH=../ && \

    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini ./talent-uwsgi.ini