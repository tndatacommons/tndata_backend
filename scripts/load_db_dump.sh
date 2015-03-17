#!/bin/bash

# IF there's a `dump.sql` file in the same directory, just load it up!
# so get rid of that.
if [ -e "/vagrant/dump.sql" ]
    then
    sudo -u postgres dropdb tndata_backend;
    sudo -u postgres createdb -E UTF8 -T template0 tndata_backend
    sudo -u postgres psql -h 127.0.0.1 -U tndata_backend -d tndata_backend -f /vagrant/dump.sql
else
    echo
    echo "Could not find a DB dump.sql file!"
    echo
fi
