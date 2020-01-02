### Brief
The ultimate aim is to be able to access Bokeh models individually from a document so that I can make use of HTML templates and CSS. This is possible with static plots and the Jinja templates; however, I want to use linked dynamic plots embedded in a Flask framework.

In the setup I have at the moment, I run a Bokeh server in parallel to Flask, then I use the ```server_session``` function to get a self-replacing script that embeds a Bokeh document in the page. I then place this script in an HTML template. This works fine when I want to embed the whole document, but when I pass a specific model that I want to embed, the ```server_session``` keeps getting the whole document regardless of what I pass to the ```model``` parameter. [This issue on Stack Overflow](https://stackoverflow.com/questions/52861629/embed-bokeh-server-with-multiple-roots-in-django) is essentially the same problem, but it remains unanswered as I am writing this.

Below is a minimal example where I experience the issue.

### Setup
* Python 3.7
* Bokeh 1.4.0
* Flask 1.1.1


### Code to reproduce issue
Contents of ```simple-app.py```:
```
from flask import Flask, render_template
from tornado.ioloop import IOLoop
from bokeh.server.server import Server
from bokeh.plotting import figure
from bokeh.embed import server_session
from bokeh.client import pull_session
from threading import Thread


app = Flask(__name__)


def bokeh_document(curdoc):
    """
    A simple Bokeh document with two models.
    """
    p1 = figure(name="blue_circle")
    p1.circle(1, 1, size=10, color='blue')
    p2 = figure(name="red_circle")
    p2.circle(1, 1, size=10, color="red")
    curdoc.add_root(p1)
    curdoc.add_root(p2)


def start_bokeh_server():
    """
    Start the Bokeh Server in a daemon thread.
    """
    bk_server = Thread(target=bokeh_server, args=[bokeh_document])
    bk_server.daemon = True # Set to True so it stops when the main thread reaches its end
    bk_server.start()


def bokeh_server(bokeh_app):
    server = Server(
        {"/bkapp": bokeh_app},
        ioloop=IOLoop(),
        allow_websocket_origin=["127.0.0.1:8000"]
    )
    server.start()
    server.io_loop.start()


@app.route('/', methods=['GET'])
def bkapp_page():
    with pull_session(url='http://localhost:5006/bkapp') as session:
        doc = session.document
        blue_circle_plot = doc.get_model_by_name("blue_circle")
        red_circle_plot = doc.get_model_by_name('red_circle')
        script = server_session(model=blue_circle_plot, session_id=session.id, url='http://localhost:5006/bkapp')

    return render_template("index.html", selected_plot=script, template="Flask")


if __name__ == "__main__":
    start_bokeh_server()
    app.run(port=8000)

```

Contents of ```templates\index.html```:
```
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
  </head>
  <body>

  <div>

    {{ selected_plot | safe }}

  </div>

  </body>
</html>
```

Run with ```python simple-app.py```

#### Screenshots
In the below screenshot, I only expect the plot with the blue dot to appear:

![image](https://user-images.githubusercontent.com/13452842/71684621-ea22a880-2d8d-11ea-80a1-d4be1a0ac625.png)

### Possible cause
I looked through the code a bit, and think the problem might lie with the ```autoload_tag.html``` template ([see here](https://github.com/bokeh/bokeh/blob/master/bokeh/core/_templates/autoload_tag.html). I notice  that in the last line, the script tag does not actually reference the ```modelid``` parameter.