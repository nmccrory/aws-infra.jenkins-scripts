#!/bin/bash -xe

env

PRIVATEIP=$(knife search node "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'cd /var/www/ && for d in */ ; do if test -f /var/www/$d/current/docroot/sites/default/settings.php; then echo "$d"; drush -r /var/www/$d/current/docroot ups; fi done'