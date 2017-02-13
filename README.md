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

*Note*: This project also uses postgres, redis, and elasticearch, so you'll
also need those services available to work on everything.

Apps
----

This project contains the following private apps, contained in the `tndata_backend`
directory.

- `badgify_api`: An API ship on top of the `django-badgify` app. This app
  expopses badgify details using django-rest-framework.
- `chat`: A simple chat app powered by websockets (using django-channels)
- `goals`: This app contains the bulk of this project's features including
  a library of goal content and the api to serve it to the mobile app.
- `notifications`: The laster that interacts with GCM and APNS. It contains
  tools to create and queue push notifications that should be delivered.
- `officehours`: MVP app whose intention is to connect students with teachers
  via their officehours and courses.
- `questions`: a simple Quora/Stackoverflow clone targetted at students.
- `rewards`: Models and api for misc reward content, such as quotes, jokes, etc.
- `survey`: (*unused*) Models, views, and api for surveys.
- `userprofile`: This app contains user profile-related models and apis. This
  project uses django's built-in User model, and this app is an extension for
  user-related data.
- `utils`: Misc utillities that are used across other apps in this project.

License
-------

This project is distributed under the terms of the MIT license. See the
LICENSE.md file in this repo.
