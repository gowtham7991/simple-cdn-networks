#!/bin/bash
REPLICA_SERVERS=("proj4-repl1.5700.network" "proj4-repl2.5700.network" "proj4-repl3.5700.network" "proj4-repl4.5700.network" "proj4-repl5.5700.network" "proj4-repl6.5700.network" "proj4-repl7.5700.network")
preload=`cat ./preload_files.txt|tr '\n' ';'`
for repl in "${REPLICA_SERVERS[@]}"
do
	echo "Deploying to $repl"
	ssh -i ~/.ssh/id_ed25519 dkgp@$repl "pkill -u dkgp httpserver"
	# scp -i ~/.ssh/id_ed25519 -r disk/ dkgp@$repl:
	scp -i ~/.ssh/id_ed25519 -r server/target/release/httpserver dkgp@$repl:
	ssh -i ~/.ssh/id_ed25519 dkgp@$repl "screen -d -m ./httpserver -p 25015 -o http://cs5700cdnorigin.ccs.neu.edu:8080/" 
done
for repl in "${REPLICA_SERVERS[@]}"
do
	echo "Preloading $repl"
	curl --data $preload $repl:25015/preload
done
echo "Allow 10 minutes for cache to warm up."