FROM nikolaik/python-nodejs:python3.10-nodejs19

# Debian "buster" reached end-of-life and was moved off the normal mirrors,
# so apt-get update 404s against deb.debian.org. Point it at
# archive.debian.org instead, and temporarily skip the extra nodesource/yarn
# repo files (broken/unsigned) since we only need ffmpeg from Debian itself.
RUN mv /etc/apt/sources.list.d /etc/apt/sources.list.d.bak \
    && sed -i \
       -e 's|deb.debian.org|archive.debian.org|g' \
       -e 's|security.debian.org|archive.debian.org|g' \
       /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mv /etc/apt/sources.list.d.bak /etc/apt/sources.list.d

COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir -U -r requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
RUN pip3 install --no-cache-dir --upgrade youtubesearchpython  # <--- यह लाइन डालें

CMD ["bash", "start"]
