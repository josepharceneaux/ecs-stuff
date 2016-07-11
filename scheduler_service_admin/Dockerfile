FROM gettalent/base-service-container:latest

WORKDIR /root/base_service_container
ADD . scheduler_service_admin
WORKDIR /root/base_service_container/scheduler_service_admin

EXPOSE 80

# Install the tools we need to build
RUN apt-get update
RUN apt-get install -y nodejs
RUN apt-get install -y npm
RUN ln -s /usr/bin/nodejs /usr/bin/node

RUN npm install -g bower
RUN npm install -g gulp
RUN npm install gulp
RUN npm install yargs
RUN npm install
RUN bower --allow-root install

# Build and start node server
RUN gulp build
CMD gulp serve-build
