#!/bin/bash
# Fix PostgreSQL in WSL to accept connections from Windows

echo "================================================"
echo "PostgreSQL WSL Configuration Fix"
echo "================================================"
echo ""
echo "This script will configure PostgreSQL in WSL to accept connections from Windows."
echo "You may be prompted for your sudo password."
echo ""

# Update listen_addresses
echo "[1/3] Updating listen_addresses..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/16/main/postgresql.conf
echo "   Done"

# Add pg_hba.conf entry for Windows connection
echo "[2/3] Updating pg_hba.conf to allow Windows connections..."
if ! grep -q "host.*all.*all.*172.22.0.0/16.*md5" /etc/postgresql/16/main/pg_hba.conf; then
    echo "host    all             all             172.22.0.0/16           md5" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf > /dev/null
    echo "   Added Windows network to pg_hba.conf"
else
    echo "   Windows network already in pg_hba.conf"
fi

# Restart PostgreSQL
echo "[3/3] Restarting PostgreSQL..."
sudo service postgresql restart
echo "   PostgreSQL restarted"

echo ""
echo "================================================"
echo "Configuration Complete!"
echo "================================================"
echo ""
echo "PostgreSQL should now accept connections from Windows"
echo "Connection string: postgresql://fbauto:kasing@172.22.0.181:5432/ad_reporting"
echo ""
