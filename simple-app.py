# Things to say:
# Duplicate question: https://stackoverflow.com/questions/52861629/embed-bokeh-server-with-multiple-roots-in-django
# Setting simple IDs does not help
# Tried looking at template - modelid does not seem to be used?
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
    p1.circle(1, 1, size=100, color='blue')
    p2 = figure(name="red_circle")
    p2.circle(1, 1, size=100, color="red")
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
    """
    See https://stackoverflow.com/questions/42958384/entry-point-for-a-bokeh-server
    for example and explanation.
    """
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
