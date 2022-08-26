from flask import Flask, render_template, redirect, url_for, Response, request, session
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import plotly
import plotly.express as px


app = Flask(__name__,template_folder='templates')

def water_graph(city):
    dp = pd.read_csv('D:/Hackathons/psg/water.csv',encoding= 'unicode_escape')
    dp2 = dp[dp['District Name']==city].reset_index()
    la = []
    la = dp2['Quality Parameter'].unique()
    val = dp2['Quality Parameter'].value_counts()
    fig = go.Figure(data=[go.Pie(labels=la, values=val, hole=.3)])
    #fig.show()
    plot_w = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return plot_w


def air_graph(labels,values):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    #fig.show()
    plot_air = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return plot_air

#l = ["CO","NO2","OZONE","PM10","PM25","SO2"]
#v = [1.453,25.291,8.032,52.24,21.943,1.898]
#air_graph(l,v)

df = pd.read_csv('D:/Hackathons/Delta/water.csv',encoding= 'unicode_escape')

#Encoding The IteM Type Column
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
encoded_state = le.fit_transform(df['State Name'])
df['encoded_state'] = encoded_state

encoded_city = le.fit_transform(df['District Name'])
df['encoded_city'] = encoded_city

encoded_quality = le.fit_transform(df['Quality Parameter'])
df['encoded_quality'] = encoded_quality

feature_columns=['encoded_state', 'encoded_city']
x = df[feature_columns].values
y = df['encoded_quality'].values

from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size = 0.2, random_state = 3)

from sklearn.neighbors import KNeighborsClassifier
classifier = KNeighborsClassifier(n_neighbors=5)
classifier.fit(x_train, y_train)

df2 = df.groupby('State Name').agg('first').reset_index()
df2 = df2.drop(['District Name','encoded_city','encoded_quality','Block Name','Quality Parameter','Panchayat Name', 'Village Name', 'Habitation Name', 'Year'], axis = 1)

df3 = df.groupby('District Name').agg('first').reset_index()
df3.drop(['State Name','encoded_state','encoded_quality','Block Name','Quality Parameter','Panchayat Name', 'Village Name', 'Habitation Name', 'Year'], axis = 1)

def predict(inp):
    state, city = inp
    st  = df2[df2['State Name'] == state].index[0]
    ct  = df3[df3['District Name'] == city].index[0]
    x_new=[[st,ct]]
    pred_new = classifier.predict(x_new)  
    return pred_new
# ROUTES
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/airquality')
def airquality():
    return render_template('main_a.html')

@app.route('/waterquality')
def waterquality():
    return render_template('main_w.html')

@app.route("/water", methods=["GET", "POST"])
def water():
    state = request.form['state']
    state = state.upper()
    city = request.form['city']
    city = city.upper()
    features = []
    features.append(state)
    features.append(city)
    output = predict(features)
    if output == 0:
        chem = "Arsenic"
    elif output == 1:
        chem = "Fluoride"
    elif output == 2:
        chem = "Iron"
    elif output == 3:
        chem = "Nitrate"
    else:
        chem = "Salt"
    plot_w = water_graph(city)
    return render_template("success_w.html", p_text='The Dominant Chemical in the Water of your Area is  {}'.format(chem), graphJSON=plot_w)    


@app.route("/air", methods=["GET", "POST"])
def air():
    city = request.form['city']
    city = city.upper()
    url = "https://api.ambeedata.com/latest/by-city"
    querystring = {"city":city}
    headers = {
        'x-api-key': "45bc722a000629ee4bb92e0158710002d1c69cafa0b199e6f262a6ad46b4d9d0",
        'Content-type': "application/json"
        }
    response = requests.request("GET", url, headers=headers, params=querystring)
    #print(response.text)
    r = response.json()
    lab = r.get("stations")
    temp = list(lab[0].keys())
    labels = temp[:6]
    labels.pop(2)
    aqiInfo = lab[0].get("aqiInfo")
    cat = aqiInfo['category']
    mp = aqiInfo['pollutant']
    Aqi = lab[0].get("AQI")
    temp.clear()
    temp = list(lab[0].values())
    values = temp[:6]
    values.pop(2)
    plot_air = air_graph(labels,values)
    return render_template("success_a.html", graphJSON=plot_air, aqi = Aqi, cat = cat, mp = mp) 

@app.route("/soil", methods=["GET", "POST"])
def soil():
    lat = request.form['lat']
    lng = request.form['lng']
    url = "https://api.ambeedata.com/soil/latest/by-lat-lng"
    querystring = {"lat":lat,"lng":lng}
    headers = {
        'x-api-key': "45bc722a000629ee4bb92e0158710002d1c69cafa0b199e6f262a6ad46b4d9d0",
        'Content-type': "application/json"
        }
    response = requests.request("GET", url, headers=headers, params=querystring)
    #print(response.text)
    return render_template("success_s.html")  

@app.route("/ozone", methods=["GET", "POST"])
def ozone():
    city = request.form['city']
    city = city.upper()
    url = "https://api.ambeedata.com/ghg/latest/by-place"
    querystring = {"place":city}
    headers = {
        'x-api-key': "45bc722a000629ee4bb92e0158710002d1c69cafa0b199e6f262a6ad46b4d9d0",
        'Content-type': "application/json"
        }
    response = requests.request("GET", url, headers=headers, params=querystring)
    #print(response.text)
    return render_template("success_o.html") 
if __name__ == "__main__":
    app.run(debug=True)