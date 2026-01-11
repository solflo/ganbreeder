# Ganbreeder

> [Ganbreeder](https://ganbreeder.app) is a collaborative art tool for discovering images. Images are 'bred' by having children, mixing with other images and being shared via their URL. This is an experiment in using breeding + sharing as methods of exploring high complexity spaces. GAN's are simply the engine enabling this. Ganbreeder is very similar to, and named after, Picbreeder. It is also inspired by an earlier project of mine [Facebook Graffiti](http://www.joelsimon.net/facebook-graffiti.html) which demonstrated the creative capacity of crowds. Ganbreeder uses [these](https://tfhub.dev/deepmind/biggan-128/2) models.

> This code was made in a weekend and hasn't been cleaned up or documented yet. There are also improvements to make to scalability.

this repo has the changes to make it work for me in 2026. 

## How to use

### Prerequisites
* Install Python 3.7 + pip (for the GAN server)
* Install NodeJS + npm (for the frontend)
* Install a PostgreSQL server

### Launch the GAN server

do this on a venv okay? easiest way is with [uv](https://docs.astral.sh/uv/getting-started/installation/): ```uv venv --python 3.7```

```bash
cd gan_server
# Install dependencies
pip install -r requirements.txt
# And go...
python server.py
```
Your GAN server is available at http://localhost:5000/

### Configure the frontend
For quick hacking, if you have Docker at your disposal, you can spawn a PostgreSQL database like so:
```bash
docker run -p 5432:5432 --name ganbreederpostgres -e POSTGRES_PASSWORD=ganbreederpostgres -d postgres
```
With that simple scenario, the database and user would be `postgres` and the password would be `ganbreederpostgres`

Copy the file `server/example_secrets.js` to `secrets.js` and modify it to fit your environment. <- this means adding ```database```, ```user``` and ```password``` to that thangg. and possibly other things, but again, we're running things locally and security is irrelevant.

### Launch the frontend
```bash
cd server
npm install
# Create the database structure
node_modules/knex/bin/cli.js migrate:latest
# Generate the first images
node make_randoms.js
# Generate a cache of image keys for the front page (do it every time you want to update the front page)
node updatecache.js
# And go...
node server.js
```
Your frontend is available at http://localhost:8888/

## docker-compose setup (alternative?)

i couldn't make this work, but i think i just messed up in a very obvious and stupid way. currently this is the _original_ image, using older dependencies and python 3.6. shouldn't make a difference ofc. 

Make sure that [docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/install/) are installed.

Start the containers:
```bash
docker-compose up
```
Your frontend is available at http://localhost:8888/, backend at http://localhost:5000/.
Initial backend setup can take few minutes.

If this is the first time you are running the project you might want to generate some random images:
```bash
docker-compose exec server node make_randoms.js
```
Restart only frontend server (to avoid backend initialization wait):
```bash
docker-compose restart server
```
