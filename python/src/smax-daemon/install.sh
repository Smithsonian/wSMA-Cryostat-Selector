#!/bin/bash
#
# Install, enable and run the Selector SMAX Daemon service with systemd
# as a user service.
# 
# Paul Grimes
# 09/23/2024
#

USER_LOCAL_LIB="/opt/wSMA"
INSTALL="$USER_LOCAL_LIB/selector_smax_daemon"
CONFIG="/home/smauser/wsma_config"

mkdir -p $INSTALL
mkdir -p "$CONFIG/cryostat/selector"

cp "./selector_smax_daemon.py" $INSTALL
cp "./selector_interface.py" $INSTALL
cp "./selector_smax_daemon.service" $INSTALL
cp "./on_start.sh" $INSTALL

chmod -R 755 $INSTALL
chown -R smauser:smauser $INSTALL

ln -s "$INSTALL/selector_smax_daemon.service" "/etc/systemd/system/selector_smax_daemon.service"

if ! test -f "$CONFIG/smax_config.json"
then
    cp "./smax_config.json" $CONFIG
fi

if ! test -f "$CONFIG/cryostat/selector/selector_config.json"
then
    cp "./selector_config.json" "$CONFIG/cryostat/selector"
    cp "./log_keys.conf" "$CONFIG/cryostat/selector"
else
    read -p "Overwrite selector_config.json and log_keys.conf? " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        cp "./selector_config.json" "$CONFIG/cryostat/selector"
        cp "./log_keys.conf" "$CONFIG/cryostat/selector"
    fi
fi

chmod -R 755 $CONFIG
chown -R smauser:smauser $CONFIG

read -p "Enable selector_smax_daemon at this time? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    systemctl daemon-reload
    systemctl enable selector_smax_daemon
    systemctl restart selector_smax_daemon
fi

exit
