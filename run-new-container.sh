#! /bin/bash
#__BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#__END_LICENSE__

getopts "a:" addropt

# If we are running on a separate IP, we can use the standard SSH port, otherwise
# we default to a non-standard port (222) so we don't interfere with host SSH.
sshport=222

if [ "$OPTARG" ]; then
    address="$OPTARG:"
    sshport=22
   shift $((OPTIND - 1))
fi

if [ $# -lt 2 -o $addropt = "?" -a $OPTIND -eq 2 ]; then
  echo "Usage:"
  echo "$0 [-a forwardIP] <new-container-name> <image-name> [<data-store-name> [<host-source-path>:<container-source-path> ...]]"
  exit 1
fi

container_name=$1
image_name=$2

if [ $# -gt 2 ]; then
   data_store_name=$3
fi

if [ $# -eq 2 ]; then
  echo "Starting *without* data container or mapping host source to docker."
  echo "Container name: $container_name"
  echo "Image name: $image_name"
  docker run -t -d --name $container_name --hostname $container_name -p ${address}80:80 -p ${address}3306:3306 -p ${address}7500:7500  -p ${address}${sshport}:22 -p ${address}443:443 -p ${address}3001:3001 -p ${address}5000:5000 -p ${address}5984:5984 -p ${address}8080:8080 -p ${address}8181:8181 -p ${address}9090:9090 -p ${address}9191:9191 $image_name
fi

if [ $# -eq 3 ]; then
  echo "Starting with data container $data_store_name and *no* source mapping."
  echo "Container name: $container_name"
  echo "Data store container: $data_store_name"
  echo "Image name: $image_name"
  docker run -t -d --volumes-from $data_store_name --name $container_name --hostname $container_name -p ${address}80:80 -p ${address}3306:3306 -p ${address}7500:7500  -p ${address}${sshport}:22 -p ${address}443:443 -p ${address}3001:3001 -p ${address}5000:5000 -p ${address}5984:5984 -p ${address}8080:8080 -p ${address}8181:8181 -p ${address}9090:9090 -p ${address}9191:9191 $image_name
fi

if [ $# -gt 3 ]; then
    dir_mappings=""
    shift 3  # drop previously parsed args
    while (( "$#" )); do
        dir_mappings+="-v $1 "
        shift
    done
fi

if [ -n "$dir_mappings" ]; then
  echo "Starting with data container $data_store_name and source mapping(s): $dir_mappings"
  echo "Container name: $container_name"
  echo "Data store container: $data_store_name"
  echo "Image name: $image_name"
  echo "Source mappings: $dir_mappings"
  docker run -t -d $dir_mappings --volumes-from $data_store_name --name $container_name --hostname $container_name -p ${address}80:80 -p ${address}3306:3306 -p ${address}7500:7500  -p ${address}${sshport}:22 -p ${address}443:443 -p ${address}3001:3001 -p ${address}5000:5000 -p ${address}5984:5984 -p ${address}8080:8080 -p ${address}8181:8181 -p ${address}9090:9090 -p ${address}9191:9191 $image_name
fi
