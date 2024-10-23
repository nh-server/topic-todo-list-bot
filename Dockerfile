FROM python:3.11-slim
ENV IS_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME /home/intmodmail
RUN useradd -m -d $HOME -s /bin/sh intmodmail
WORKDIR $HOME
COPY ./requirements.txt .
RUN pip install --no-compile --no-cache-dir -r requirements.txt
USER intmodmail
RUN mkdir -p ./data/logs
RUN touch ./data/logs/main.log
RUN touch ./data/logs/sql.log
COPY . .
CMD ["python3", "main.py"]
