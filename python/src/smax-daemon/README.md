# lakeshore-smax-daemon

A systemd service implemented in Python that reads values from the wSMA cryostat compressor control and readout, and writes the data to SMAx.

Configuration of the daemon is set in the JSON format config file `compressor_config.json`.

Service structure is based on tutorials at https://alexandra-zaharia.github.io/posts/stopping-python-systemd-service-cleanly/ and https://github.com/torfsen/python-systemd-tutorial

Service is set up to use `SIGINT` to safely stop the process.  This is caught with a `try/except` statement around the service event loop as `KeyboardInterrupt`, allowing closing of open pipes and files, and other shutdown procedures to be called.

Installation as both a user and system service is described in the second tutorial.

Requires:
systemd-python (in turn requires linux pacakage systemd-devel)
psutils
wSMA-Cryostat-Compressor wsma_cryostat_compressor module
smax-python