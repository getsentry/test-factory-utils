FROM python:3.8.12

WORKDIR /work

RUN pip install -U pip==22.0.4

# Install requirements first to optimize layer caching
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

COPY . ./

ENTRYPOINT ["waitress-serve", "--listen", "127.0.0.1:8080", "--call", "app:get_app"]
