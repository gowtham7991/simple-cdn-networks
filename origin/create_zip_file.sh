#!/bin/bash

rm disk.tar
files=`cat ../brainstorming/disk_files.txt | awk '{print "./"$0}'| tr '\n' ' '`
# brotli -Z $files
files=`cat ../brainstorming/disk_files.txt | awk '{print "./"$0".br"}'| tr '\n' ' '`
tar caf disk.tar $files
# 7z a -t7z -m0=LZMA2 -mmt=on -mx9 -md=64m -mfb=64 -ms=16g -mqs=on -sccUTF-8 -bb0 -bse0 -bsp2 disk.7z $files