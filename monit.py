#!/usr/bin/env python
import sys
from flask import Flask
from flask import request
from flask import render_template
from flask import make_response
from flask import redirect, url_for
from flask import session
from flask import flash
from flask import Response

from datetime import datetime
import time
import psutil
import re

app = Flask(__name__)
app.secret_key = '\xb4\x9e\x9e\xd07\x17\xfe\xe1\xf6n\xe0\xf4\x87\x08\xc2\xc4k\xbb\xb2ru\xac{>'

@app.route('/')
def index():
    return redirect(url_for('monit'))

@app.route('/test')
def test():
    # home page of the site
    return render_template('monit_index.html')

@app.route('/monit')
def monit():
    try:
        username = session['username']
    except KeyError, ke:
        username = None
    if username is None:
        return redirect(url_for('login'))
    users = len(psutil.users())
    mysql_running = psutil.pid_exists(18685)
    boottime, num_cpus = psutil.BOOT_TIME, psutil.NUM_CPUS
    uptime = datetime.fromtimestamp(boottime).strftime("%Y-%m-%d %H:%M:%S")
    data = {
        'users' : users,
	'uptime' : uptime,
	'num_cpus' : num_cpus
    }
    proc_list = []
    for proc in psutil.process_iter():
        pid, username, create_time, cpu_percent, cmdline = proc.pid, proc.username(), datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"), proc.cpu_percent(), proc.cmdline()
        if len(cmdline) > 1:
            proc_list.append([pid, username, create_time, cpu_percent, cmdline])
    data['proc'] = proc_list 
    data['num_proc'] = len(proc_list) 
    return render_template('monit.html', data=data)    

@app.route('/login', methods=['GET', 'POST'])
def login():
    # make POST request for login
    # access login form attributes
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
	    app.logger.error("Invalid username/password")
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # logout. remove username from session
    session.pop('username', None)
    session.pop('logged_in', None)
    flash('Your were logged out')
    return redirect(url_for('monit'))

@app.route('/sse-demo')
def sse():
    def g():
        for i, c in enumerate("hello"*10):
            time.sleep(.5)  # an artificial delay
            yield i, c
    return Response(stream_template('sse_demo.html', data=g()))

@app.route('/search', methods=['GET', 'POST'])
def search():
    error = None
    if 'search_text' in request.form:
        searched = request.form['search_text']
        app.logger.debug("Searching %s ..." % searched)
        if searched:
	    return proc(searched)
        else:
	    error = 'Invalid params. Valid param: search_text'
    return render_template('search.html', error=error)
     
# customizing the error 404 page. 
# Use errorhandler() decorator
@app.errorhandler(404)
def page_not_found(error):
    content = render_template('page_not_found.html', error=error)
    return make_response(content, error.code)

def valid_login(username, password):
    # demo validate login
    if password == '123':
        return True
    return False

def log_the_user_in(username):
    # sample: after login action
    session['username'] = username
    session['logged_in'] = True
    flash('Welcome %s! You just logged in' % username)
    app.logger.debug("%s user logged in", username)
    return redirect(url_for('monit'))

def proc(data):
    # search for pid, process_name, user etc. 
    # find pids and show process details
    proc_list = []
    flash('Search results for "%s"' % data)
    for proc in psutil.process_iter():
        pid, username, create_time, cpu_percent, cmdline = proc.pid, proc.username(), datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"), proc.cpu_percent(), proc.cmdline()
        data = data.lower()
        if (data == str(pid) or data in [str(i).lower() for i in cmdline] or data in str(username).lower()) and cmdline:
            proc_list.append([pid, username, create_time, cpu_percent, cmdline])
    data = {}
    if proc_list:
        data['proc'] = proc_list
        data['num_proc'] = len(proc_list)
    return render_template('monit.html', data=data)

def stream_template(template_name, **context):
    # http://flask.pocoo.org/docs/patterns/streaming/#streaming-from-templates
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    # uncomment if you don't need immediate reaction
    ##rv.enable_buffering(5)
    return rv


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == 'debug':    
        app.run(debug=True, port=1111)
    else:
        app.run(port=1111)
    # with debug=True, 
    # we don't have to run this module again after each change to reflect on web

