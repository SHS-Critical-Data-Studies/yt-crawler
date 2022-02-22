#!/bin/bash

cd $(dirname $0)

rm *.xpi
wget "https://addons.mozilla.org/firefox/downloads/file/3911165/ublock_origin-1.41.6-an+fx.xpi"
mv ublock_origin*.xpi ublock_origin.xpi