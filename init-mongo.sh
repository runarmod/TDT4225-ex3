# Taken directly from Stack Overflow, but had to change `mongo` to `mongosh` on line 8.
# Source - https://stackoverflow.com/a/66468323
# Posted by Lazaro Fernandes Lima Suleiman
# Retrieved 2026-10-22, License - CC BY-SA 4.0

set -e

mongosh <<EOF
use $MONGO_INITDB_DATABASE

db.createUser({
  user: '$MONGO_INITDB_USER',
  pwd: '$MONGO_INITDB_PWD',
  roles: [{
    role: 'readWrite',
    db: '$MONGO_INITDB_DATABASE'
  }]
})
EOF
