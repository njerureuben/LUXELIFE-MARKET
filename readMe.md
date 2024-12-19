# Django Deployment with Gunicorn and Whitenoise
This guide outlines the setup of Gunicorn and Whitenoise for deploying Django applications. These tools simplify deployment and ensure your app is production-ready.

## Installation
### 1. Install Whitenoise
Whitenoise is a Python package used to serve static files directly from your Django application. It eliminates the need for an external web server (like Nginx or Apache) to handle static files.

#### pip install whitenoise

### 2. Install Gunicorn
Gunicorn is a Python WSGI HTTP server for running web applications. It acts as a production-ready HTTP server to serve your Django app.
#### pip install gunicorn

### Checking Installed Dependencies
To check all installed packages and their versions, run:

#### pip freeze


# Why Use Whitenoise?
#### Whitenoise simplifies serving static files in production by:

Eliminating the Need for Nginx: Serves static files directly from Django.
Compression Support: Automatically compresses files for better performance.
Ease of Use: Works seamlessly with WSGI servers like Gunicorn.

# Why Use Gunicorn?
#### Gunicorn is a lightweight and easy-to-use HTTP server for Python web apps. It:

Efficiently handles HTTP requests.
Is production-ready, unlike Django’s development server.
Supports multiple workers for concurrent request handling.


### Ensure that also the pymysql has been installed 
This  handles the database/ server


### Add the Whitenoise to the middle where
'whitenoise.middleware.WhiteNoiseMiddleware',

### Whitenoise to Installed Apps


### Static Files
Add the code : 
##### STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
##### STATIC_ROOT = BASE_DIR / 'staticfiles'


#### Back to Terminal
python manage.py collectstatic


# Create a ProcFile
New-Item -Path . -Name "Procfile" -ItemType "File"

This will contain the following commands: 
web: gunicorn APPNAME.wsgi --log-file
web: python manage.py migrate && gunicorn APPNAME.wsg

# Create runtime.txt
This contains:
python 3.13.1 ( The python version one is using)

# Run the command: pip freeze > requirements.txt
This creates a file with all the requirements

#### Create a SHH Key
deactivate your virtual env
PS C:\Users\USER\Desktop\Luxelifev2> cd ~
PS C:\Users\USER> pwd

Path         
----         
C:\Users\USER


PS C:\Users\USER> mkdir .shh
PS C:\Users\USER> cd .ssh
PS C:\Users\USER\.ssh> ssh-keygen.exe

PS C:\Users\USER\.ssh> & ls
PS C:\Users\USER\.ssh> cat id_ed25519.pub

