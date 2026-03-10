#!/usr/bin/env bash
data="$HOME/.gitodo"
read -p "Folder to store app data [$data]:" input
data=${input:-$data}

settings="$HOME/.config/gitodo/settings.toml"
mkdir "$HOME/.config/gitodo/"
echo "[folders]" > $settings

mkdir -p $data

repo="$data/repo/"
read -p "Folder to store the git storage [$repo]:" input
repo=${input:-$repo}
mkdir -p $repo
echo "repo=\"$repo\"" >> $settings

image="$data/image/"
read -p "Folder to store positive images [$image]:" input
image=${input:-$image}
mkdir -p $image
echo "image=\"$image\"" >> $settings

sad_image="$data/sad_image"
read -p "Folder to store nefative images [$sad_image]:" input
sad_image=${input:-$sad_image}
mkdir -p $sad_image
echo "sad_image=\"$sad_image\"" >> $settings

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
ln -sf "$SCRIPT_DIR/gd.sh" ~/.local/bin/gd






