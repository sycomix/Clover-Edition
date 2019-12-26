#!/usr/bin/env bash
cd "$(dirname "${0}")"
BASE_DIR="$(pwd)"

# destination folder inside models directory
MODELS_DIRECTORY=models
MODEL_VERSION=pytorch-gpt2-xl-aid2-v5

# torrent to download
MODEL_TORRENT_URL="https://raw.githubusercontent.com/cloveranon/Clover-Edition/master/model.torrent"
MODEL_SHA_URL="https://raw.githubusercontent.com/cloveranon/Clover-Edition/master/model.sha1"
MODEL_SHA_NAME=$(basename "$MODEL_TORRENT_SHA")
MODEL_TORRENT_NAME=$(basename "$MODEL_TORRENT_URL")

# The name of the (source) folder when the torrent downloads
MODEL_TORRENT_BASENAME=model_v5_pytorch 

download_torrent() {
  echo "Creating directories."
  mkdir -p "${MODELS_DIRECTORY}"
  cd "${MODELS_DIRECTORY}"
  wget "${MODEL_TORRENT_URL}"
  wget "${MODEL_SHA_URL}"
  which aria2c > /dev/null
  if [ $? == 0 ]; then
    echo -e "\n\n==========================================="
    echo "We are now starting to download the model."
    echo "It will take a while to get up to speed."
    echo "DHT errors are normal."
    echo -e "===========================================\n"
    aria2c \
      --max-connection-per-server 16 \
      --split 64 \
      --bt-max-peers 500 \
      --seed-time=0 \
      --summary-interval=15 \
      --disable-ipv6 \
      ${MODEL_TORRENT_NAME}
    mv "${MODEL_TORRENT_BASENAME}" "${MODEL_VERSION}"
    sha1sum -c ${MODEL_SHA_NAME}
    echo "Download Complete!"
    fi
}

redownload () {
	echo "Deleting $MODEL_DIRECTORY"
	rm -rf ${MODELS_DIRECTORY}
	download_torrent
}
ls "${MODELS_DIRECTORY}/${MODEL_VERSION}"

if [[ -d "${MODELS_DIRECTORY}/${MODEL_VERSION}" ]]; then
	ANSWER="n"
	echo "Clover-Edition Model appears to be downloaded."
	echo "Would you like to redownload?"
	echo "WARNING: This will remove the current model![y/N]"
	read ANSWER
	ANSWER=$(echo $ANSWER | tr '[:upper:]' '[:lower:]')
	case $ANSWER in
		 [yY][eE][sS]|[yY])
			redownload;;
		*)
			echo "Exiting program!"
			exit;;
	esac
else
	download_torrent
fi
