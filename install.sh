#!/bin/bash
printf "Installing Packages...\n"
apt-get install -y python nmap dnsutils mtr python-pip && pip install telepot

printf "\n\n--------------------------------\n\n"
echo "Enter your Telegram BOT Token. "
read -r TG_BOT_TOKEN

echo "bot_token = '$TG_BOT_TOKEN'" > tempconfig.py

printf "\n\n--------------------------------\n\n"
echo "Fetching last Telegram messages. This will help finding your Telegram ID."
echo "If you can't see your Telegram ID, try sending a private message to this bot."
python get-sender-id.py  | grep "'id'" | uniq -c | awk '{ print $3 }' | sed s'/,//'
rm tempconfig.py

echo "Enter your Telegram ID. This will be the default admin user."
read -r SENDER_ID

cp config.example.py config.py
sed -i s"/MY-TG-BOT-TOKEN/$TG_BOT_TOKEN/" config.py
sed -i s"/MY-SENDER-ID-LIST/$SENDER_ID/" config.py

printf "\n\n--------------------------------\n\n"
echo "Do you want to configure the daemon with systemctl? (y/n)"
read -r DAEMON
case $DAEMON in
N|n)
	exit 0
	;;
Y|y)
	cp systemctl/rpgbot.example.service /tmp/rpgbot.service
	DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
	sed -i s"#MY-PATH#$DIR#" /tmp/rpgbot.service
	mv /tmp/rpgbot.service /etc/systemd/system/multi-user.target.wants/rpgbot.service
	systemctl daemon-reload
	systemctl restart tsh
	;;
*)
	echo Unrecognized option $DAEMON, exiting
	exit 1
	;;
esac
