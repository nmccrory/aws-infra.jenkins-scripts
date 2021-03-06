#!/bin/bash
if [ -z "$1" -o -z "$2" ]; then
  echo "This script requires that you pass in the src server and dest server to run."
  echo "Usage: ./file-system-rsync.sh SRC_SERVER DEST_SERVER"
  exit 1;
fi
SRC_SERVER=$1
DEST_SERVER=$2

# Place the SSH key on the DEST server for consumption by the rsync script
rsync --rsh 'ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" /var/jenkins_home/.ssh/aws.pem ubuntu@$SRC_SERVER:/tmp/aws.pem 

# Set the HOSTNAME for the ssh-generator
HOSTNAME=$SRC_SERVER

# Call the script and record the results
# The command expands to:
# ssh -T -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 ubuntu@web03.nmdev.us 'sudo -Eib env bash -s --' < /var/jenkins_home/workspace/jenkins-scripts/rsync.sh UBUNTU
# The '$' renders the SSH command, then you have a normal command that executes as part of the line's inherent exec call
eval "$($JENKINS_SCRIPTS/ssh-generator.sh 'rsync.sh $SRC_SERVER $DEST_SERVER' env $SRC_SERVER 'UBUNTU')"