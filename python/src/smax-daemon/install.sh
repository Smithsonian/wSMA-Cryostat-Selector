#!/bin/bash
#
# Install, enable and run the Compressor SMAX Daemon service with systemd
# as a user service.
# 
# Paul Grimes
# 06/29/2023
#

SYSDUSER="$HOME/.config/systemd/user"
INSTALL="$SYSDUSER/selector-smax-daemon"

mkdir -p $INSTALL
mkdir -p "$CONFIG/cryostat/selector"

cp "./selector-smax-daemon.py" $INSTALL
cp "./selector-smax-daemon.service" $SYSDUSER
cp "./on-start.sh" $INSTALL

if ! test -f "$CONFIG/smax_config.json"
then
    cp "./smax_config.json" $CONFIG
fi

cp "./compressor_config.json" "$CONFIG/cryostat/selector"
cp "./log_keys.conf" "$CONFIG/cryostat/selector"

chmod -R 755 $INSTALL

ln -s "$INSTALL/compressor-smax-daemon.service" "$HOME/.config/systemd/user/compressor-smax-daemon.service"

read -p "Enable compressor-smax-daemon at this time? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    systemctl --user daemon-reload
    systemctl --user enable compressor-smax-daemon
    systemctl --user restart compressor-smax-daemon
fi

exit