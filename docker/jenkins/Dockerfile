FROM quay.io/openshift/origin-jenkins
MAINTAINER EPFL ISAS-FSD <isas-fsd@groupes.epfl.ch>

COPY epfl-plugins.txt /opt/openshift
RUN /usr/local/bin/install-plugins.sh /opt/openshift/epfl-plugins.txt

# https://plugins.jenkins.io/configuration-as-code/
COPY configuration-as-code.yml /opt/openshift/configuration-as-code/configuration-as-code.yml
ENV CASC_JENKINS_CONFIG /opt/openshift/configuration-as-code/configuration-as-code.yml
