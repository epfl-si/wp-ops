FROM quay.io/openshift/origin-jenkins
MAINTAINER EPFL ISAS-FSD <isas-fsd@groupes.epfl.ch>

COPY epfl-plugins.txt /opt/openshift
RUN /usr/local/bin/install-plugins.sh /opt/openshift/epfl-plugins.txt
