FROM ubuntu:bionic as base

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -qy tzdata && \
  apt-get install -qy software-properties-common python3-software-properties && \
  apt-get update && apt-get install -qy \
  build-essential \
  wget \
  python3 \
  r-base \
  libffi-dev \
  libssl-dev \
  libjpeg-dev \
  zlib1g-dev \
  r-base \
  git \
  libpython3-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

RUN wget https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py


FROM base as build

# TODO: temporary repository
RUN git clone https://github.com/Kitware/UPennContrast/
WORKDIR /UPennContrast
RUN git checkout annotation-browser

RUN pip install -r devops/girder/annotation_client/requirements.txt
RUN pip install -e devops/girder/annotation_client/

COPY ./requirements.txt /
RUN pip install -r /requirements.txt

ENV PYTHON_BIN=python3

COPY ./entrypoint.py /

ENTRYPOINT [ "python3", "/entrypoint.py" ]
