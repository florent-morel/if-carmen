#stage 1
# Pull node
FROM python:3.11 AS pyimage

# Prepare Env
ARG ApiToken
ENV NVM_DIR=/usr/.nvm
ENV NODE_VERSION=18.17.1
ENV PROJECT_WORKSPACE=/app
# To disable deprecation warning logs of IF when it uses a model from if-unofficial-plugins, such as Teads Curve.
ENV NODE_NO_WARNINGS=1

# Create working directory
WORKDIR ${PROJECT_WORKSPACE}

# Install Python dep
COPY requirements.txt /tmp
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy full application code into working directory
COPY . .

# update permissions on IF genereated dir to allow unprivileged users to write there
RUN chmod 777 backend/src/services/carbon_service/impact_framework/files/generated

# Install lsb-release
RUN apt-get update && apt-get install -y lsb-release && apt-get clean all

# Setup IF
RUN mkdir -p $NVM_DIR && curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash \
    && \. $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && ln -s $NVM_DIR/versions/node/v$NODE_VERSION/bin/node /usr/bin/node \
    && npm install \
    && ln -s $NVM_DIR/versions/node/v$NODE_VERSION/bin/npm /usr/bin/npm \
    && ln -s $NVM_DIR/versions/node/v$NODE_VERSION/bin/npx /usr/bin/npx

RUN cd ${PROJECT_WORKSPACE}/cost-model-plugin \
    && npm install --ignore-scripts \
    && npm run build
