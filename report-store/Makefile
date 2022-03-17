_:
	exit 1

run:
	FLASK_ENV=development flask run -p 5050

mongo-server:
	docker run \
		--rm \
		-v ${PWD}/.dockervolumes/mongo:/data/db \
		--name mongo-server \
		-p 27017:27017 \
		-it \
		mongo:5.0.6

mongo-client:
	docker exec -it mongo-server mongo

py-shell:
	ipython -i .ipython/init.py
