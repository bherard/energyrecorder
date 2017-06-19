#!/bin/bash
cat > influx.cnf <<EOF
#
# SSLeay example configuration file.
#

RANDFILE                = /dev/urandom

[ req ]
default_bits            = 2048
default_keyfile         = privkey.pem
distinguished_name      = req_distinguished_name
prompt                  = no
policy			= policy_anything

[ req_distinguished_name ]
commonName                      = $HOSTNAME
EOF

openssl req -config influx.cnf  -new -x509  -days 3650 -nodes  -out  /etc/ssl/certs/influxdb.pem  -keyout  /etc/ssl/private/influxdb.key
chown root:root /etc/ssl/private/influxdb.key
chmod 644 /etc/ssl/private/influxdb.key
chown root:root /etc/ssl/certs/influxdb.pem
chmod 644 /etc/ssl/certs/influxdb.pem
