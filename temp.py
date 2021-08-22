from flask import Flask, flash, render_template, request, send_from_directory
import numpy as np
from datetime import datetime

###############################################
#          Define flask app                   #
###############################################
app = Flask(__name__) # Creating our Flask Instance
app.secret_key = 'secretKey'


@app.route('/', methods=['GET'])
def index():
    return "This is Cloudcroft Labs"


if __name__ == '__main__':
    app.run(debug=True)
