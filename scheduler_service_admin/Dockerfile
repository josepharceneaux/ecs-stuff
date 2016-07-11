FROM gettalent/base-service-container:latest

WORKDIR /root/base_service_container
ADD . scheduler_service_admin
WORKDIR /root/base_service_container/scheduler_service_admin

EXPOSE 80

# Install the tools we need to build
CMD apt-get update
CMD apt-get install -y nodejs
CMD apt-get install -y build-essential
CMD apt-get install -y npm

CMD npm install

# Build and start node server
CMD\
 export GT_ENVIRONMENT=$GT_ENVIRONMENT && gulp build
CMD\
 export GT_ENVIRONMENT=$GT_ENVIRONMENT && gulp serve-build
