#!/bin/bash
REPLICA_SERVERS=("proj4-repl1.5700.network" "proj4-repl2.5700.network" "proj4-repl3.5700.network" "proj4-repl4.5700.network" "proj4-repl5.5700.network" "proj4-repl6.5700.network" "proj4-repl7.5700.network")
preload=`cat ./preload_files.txt|tr '\n' ';'`
for repl in "${REPLICA_SERVERS[@]}"
do
	echo "Deploying to $repl"
	ssh -i ~/.ssh/id_ed25519 dkgp@$repl "pkill server"
	# scp -i ~/.ssh/id_ed25519 -r disk/ dkgp@$repl: 2>/dev/null &
	scp -i ~/.ssh/id_ed25519 -r server/target/release/server dkgp@$repl:
	ssh -i ~/.ssh/id_ed25519 dkgp@$repl "screen -d -m ./server;" 
done
for repl in "${REPLICA_SERVERS[@]}"
do
	echo "Preloading $repl"
	curl --data $preload $repl:25015/preload
done