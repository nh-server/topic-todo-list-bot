FROM python:3.8-slim
ENV IS_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME /home/intmodmail
RUN useradd -m -d $HOME -s /bin/sh intmodmail
WORKDIR $HOME
RUN apt-get update && apt-get install git -y
COPY ./requirements.txt .
RUN pip install --no-compile --no-cache-dir -r requirements.txt
USER intmodmail
RUN mkdir -p ./data/logs
RUN touch ./data/logs/main.log
COPY . .
CMD ["python3", "main.py"]