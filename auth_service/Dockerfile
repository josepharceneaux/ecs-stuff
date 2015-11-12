FROM gettalent/base-service-container:latest

# Add auth service stuff
WORKDIR /root/base_service_container
ADD . auth_service

# Use appropriate tag name according to flask app
RUN sed -i -e 's/TAG/AuthService/g' /etc/syslog-ng/syslog-ng.conf

WORKDIR /root/base_service_container/auth_service

EXPOSE 80

# Set DB connection string
ENV DB_STRING mysql://talent_web:s!web976892@livedb.gettalent.com/talent_core

# Set PYTHON PATH
ENV PYTHONPATH ../

CMD\
    eval "$(pyenv init -)" && \

    /etc/init.d/nginx restart && \

    /etc/init.d/syslog-ng restart && \

    uwsgi --env GT_ENVIRONMENT=$GT_ENVIRONMENT --env DB_STRING=$DB_STRING --ini ./talent-uwsgi.ini