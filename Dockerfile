FROM gcr.io/google-appengine/python
LABEL python_version=python3.6
RUN virtualenv --no-download /env -p python3.6

# Set virtualenv environment variables. This is equivalent to running
# source /env/bin/activate
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH
ADD requirements.txt /app/
RUN pip install -r requirements.txt
ADD . /app/

# Create credentials file
#RUN gsutil cp -r gs://quiz-app1313.appspot.com/credentials .

EXPOSE 8080
ENV NAME quiz-app
ENV GOOGLE_APPLICATION_CREDENTIALS credentials/gcp_access.json

# Install OS environments
RUN apt update
RUN apt -y install poppler-utils

CMD exec gunicorn -b :$PORT main:app
