if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/NEGANTG/masterjan30.git /masterjan30
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /masterjan30
fi
cd /masterjan30
pip3 install -U -r requirements.txt
echo "Starting Bot...."
python3 bot.py
