# Dockerfile customizations for building buildbot's CI test suite.
#
# Provided here as a real life example on how to make a customized
# worker Dockerfile for your project

FROM        tardyp/buildbot-worker:master
MAINTAINER  Buildbot Maintainers

# Switch to root to be able to install stuff
USER root

# install the DB drivers we need to test against databases, as well as git
RUN apt-get install -y libmysqlclient-dev libpq-dev git libenchant-dev python-virtualenv

# Switch to regular user for security reasons
USER buildbot
