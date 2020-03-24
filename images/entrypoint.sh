#!/bin/bash

VIRTUAL_ENV=venvdocker
MOUNTED_DIRECTORY=/outputs

# Make sure the user mounted the volume for us to build the package
[ ! -d ${MOUNTED_DIRECTORY} ] && \
    echo "You must mount the metafy directory to "\
         ${MOUNTED_DIRECTORY}\
         ". Use '-v <path-to-metafy>:" ${MOUNTED_DIRECTORY} "'" && \
    exit

# install metafy in a virtual environment
pushd ${MOUNTED_DIRECTORY}
python3 -m virtualenv ${VIRTUAL_ENV} && . ${VIRTUAL_ENV}/bin/activate
pip install . && python3 setup.py pytest && metafy build-pkg

# cleanup after ourselves
rm -rf ${VIRTUAL_ENV}
exit
