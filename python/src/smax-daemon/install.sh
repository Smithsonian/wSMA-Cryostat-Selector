#!/bin/bash
#
# Install, enable and run the Compressor SMAX Daemon service with systemd
# as a user service.
# 
# Paul Grimes
# 06/29/2023
#

INSTALL="$HOME/.config/systemd/user/compressor-smax-daemon"

mkdir -p $INSTALL

cp "./compressor-smax-daemon.py" $INSTALL
cp "./compressor-smax-daemon.service" $INSTALL
cp "./on-start.sh" $INSTALL
cp "./compressor_config.json" $INSTALL


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