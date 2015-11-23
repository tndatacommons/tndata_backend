TN Data Backend
===============

The django-powered APIs, dashboard, and metrics for TN Data Commons.


Getting Started
---------------

The easist way to get started is to use the Vagrant-powered virtual machine
in the [deployment_tools](https://bitbucket.org/tndata/deployment_tools)
repo. Once provisioned, it will contain all you need to run the development
server.

Alternatively, you can follow these steps:

1. Create a python 3 virtual environment, eg: `pyvenv-3.4 env`
2. Activate the environment: `source env/bin/activate`
3. Install the requirements: `pip install -r requirements.txt`
4. Run the development server `cd tndata_backend; python manage.py runserver`


Apps
----

This project contains the following private apps, contained in the `tndata_backend`
directory.

- `diary`: (abandoned) This was originally started as a daily diary app for
  users to record their thought, feelings, progress, whatever.
- `goals`: This app contains the bulk of this project's features including
  a library of goal content and the api to serve it to the mobile app.
- `notifications`: An app that interacts with GCM. It contains tools to create
  messages that should be delivered and the features to send them to the GCM
  service.
- `rewards`: Models and api for misc reward content, such as quotes, jokes, etc.
- `rules`: (abandoned) originally an attempt to integrate venmo's business-rules
  project to create arbitrary rules-based logic.
- `survey`: Models, views, and api for surveys.
- `tndata_backend`: This is our **project config** (which is unfortunately named)
  it contains project settings, the Root URLConf, and our wsgi file.
- `userprofile`: This app contains user profile-related models and apis. This
  project uses django's built-in User model, and this app is an extension for
  user-related data.
- `utils`: Misc utillities that are used across other apps in this project.

License
-------

This code is the property of Tennessee Data Commons.

(c) 2015 all rights reserved.
