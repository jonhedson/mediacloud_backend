Mediacloud Backend
==================

Welcome to the `mediacloud_backend` repository! In this short README you'll
find information about the project, how to install and run it.


## Introduction

This project aims to download as many feeds (RSS or Atom) as possible. This is
the "backend" of mediacloud project since the goal here is to **discover and
download** the feeds (and not to create a visualization or analyses with the
data retrieved).

The backend project is divided into 3 simple steps:

- **Step 1**: Discover Web pages that contain feed URLs (by now we use Google
  search);
- **Step 2**: Access each of the URLs retrieved above and search for feed URLs
  (like ending with `.rss`, `.atom` etc.);
- **Step 3**: Given the list of feed URLs generated by the step above, download
  all feeds.


## Installation

You can install everything in your system or create a
[Docker](http://docker.io) image using the provided `Dockerfile` - jump to
"Using Docker" if you prefer to install everything in a container instead of in
your system.

### Installing in your system

#### Compilers and needed libraries

We need to install some libraries, compiler and services. To do it on
Debian-based systems (such as Ubuntu), run as root:

    apt-get install python-dev build-essential libxml2-dev libxslt1-dev zlib1g-dev libssl-dev


#### httrac

We also need to download and compile [httrack](http://www.httrack.com/), as we
use it to crawl the Web pages. To install it, run as root:

    wget http://download.httrack.com/cserv.php3?File=httrack.tar.gz -O httrack.tar.gz
    tar xfz httrack.tar.gz
    cd httrack-*
    ./configure
    make
    make install
    ln -s /usr/local/lib/libhttrack.* /usr/lib/
    cd ..
    rm -rf httrack*


#### MongoDB

We also use [MongoDB](http://www.mongodb.org/) database (to store our data), so
you need to install and run it. On Debian/Ubuntu GNU/Linux systems, execute as
root:

    apt-get install mongodb

To verify if the installation succeeded and if it's running, execute:

    mongo

> NOTE: In the first time that you run MongoDB server (it runs automatically
> when you install it) it can take a while to preallocate database files, so
> wait for 1 or 2 minutes if the execution of `mongo` is returning an error
> such as "couldn't connect to server 127.0.0.1:27017".

If everything went fine, you'll have a MongoDB client shell connected to your
local MongoDB server (if not, an error will be displayed). To exit the shell,
just type `Ctrl+c`.


#### virtualenv and virtualenvwrapper

If you don't have virtualenv and virtualenvwrapper installed in your system,
do it before running the commands above. If you're on a Debian or Ubuntu
GNU/Linux system, just execute as root:

    apt-get install python-pip
    pip install virtualenv virtualenvwrapper

And then add to the end of your `~/.bashrc` file:

    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh

You need to reload your shell to the modifications take action or execute
`source ~/.bashrc` just after adding these lines to the file.


#### Python requirements

After having all system dependencies installed, you need to create a
virtualenv to this project and install our Python dependencies:

    mkvirtualenv mediacloud_backend
    pip install -r requirements.txt

### Using Docker

To build a new image using [Docker](http://docker.io), just execute in the root
of this repository:

    docker build -t mcb .

Then it'll build an image called `mcb` with everything you need installed (and
the code copied to `/srv/mediacloud_backend`).

To run a container from this image, execute:

    docker run -t -i mcb /bin/bash

As we don't run any service on the container by default (with the command above
you only run Bash - nothing more is run on the container), you need to run
MongoDB server before using any script that needs it. Execute on the
container's shell:

    mongod -f /etc/mongodb.conf &

Then you can go to `/srv/mediacloud_backend/capture` and run any of the scripts
there (you don't need to active a virtualenv), for example:

    cd /srv/mediacloud_backend/capture
    python googlerss.py
    python extract_feeds.py
    python downloader.py

## Using the scripts

To execute the scripts of this project you need to activate the virtualenv
created in the installation step. Do it with:

    workon mediacloud_backend


### Step 1: Search for URLs which contain links to feeds

Script usage:

    python capture/googlerss.py [-s <subject>]

This command searches Google for pages matching `RSS` and `<subject>` (if
specified), returning many pages of results. Don't run this too often if you
don't want to get your IP banned. If `<subject>` is ommited a general search
for "RSS" is done. This script only searches for sites in Brazil (domain ending
with .br).

The URLs found are inserted in a collection called `urls` (on MongoDB), which
will be used by the `capture/extract_feeds.py` script.

To check the URLs discovered, run MongoDB client with the command `mongo MCDB`
(`MCDB` is the name of the database) and execute the command `db.urls.find()`
inside MongoDB shell.


### Step 2: Search for feeds URLs

Given a list of URLs (on a text file or in a MongoDB collection), this script
fetches each URL and tries to find feed URLs inside the page. The URLs are
scanned using `httrack` and then inserted in the `feeds` collection on MongoDB
(database `MCDB`).  Feeds are checked for duplicates before insertion into the
collection.

Script usage:

    python capture/extract_feeds.py [-dN] [-f text-file-with-URLs]

The `-d` parameter specifies the depth of scanning (default is `2`).

> ATTENTION: Before executing this script, edit the file `capture/settings.py`
> and define the MongoDB server in which the feeds should be stored.


### Step 3: Download feeds

Download (in a multi-threaded way) all the feeds from the URLs discovered by
*Step 2*.

Script usage:

    python capture/dowloader.py

The articles downloaded will be stored in MongoDB collection `articles` inside
`MCDB` database.  Insertion in the database checks for duplicate URLs and
doesn't re-insert them.  We recommend that this is run as a cron job every so
often.
