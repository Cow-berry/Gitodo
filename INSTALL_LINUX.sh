#!/usr/bin/env bash
settings="$HOME/.config/gitodo/settings.toml"
touch settings
echo "[folders]" > $settings

data="$HOME/.gitodo"
read -p "Folder to store app data [$data]:" input
data=${input:-$data}
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

sad_image="$data/sad_img"
read -p "Folder to store nefative images [$sad_image]:" input
sad_image=${input:-$sad_image}
mkdir -p $sad_image
echo "sad_image=\"$sad_image\"" >> $settings

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
ln -sf "$SCRIPT_DIR/gd.sh" ~/.local/bin/gd






