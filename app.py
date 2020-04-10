# -*- coding: utf-8 -*-
from zeep import Client
from flask import Flask, request, render_template

#import keyring
import requests
from datetime import datetime, date, time
    
app = Flask(__name__)


@app.route('/')
def index():
    return render_template("Accueil.html")

@app.route('/formCalcul')
def formCalcul():
    listgare = List_Gare()
    return render_template("formCalcul.html", listgare=listgare)

@app.route('/Calcul', methods=['GET','POST'])
def Calcul():
    if request.method == 'POST':
        result = request.form
        town1 = result['town1']
        town2 = result['town2']
        daydepart = result['daydepart']
        timedepart = result['timedepart']
        devise = result['devise']
        
        distance = Calcul_distance(town1,town2)
        
        http_rest="http://trouve-ton-train-rest.herokuapp.com/CalculPrix"
        response = requests.get( http_rest, params =  {'distance' : float(distance), 'devise' : devise })
        prixtrajet = response.json()
        
        departure=daydepart+" "+timedepart
        dt = datetime.strptime(departure, "%Y-%m-%d %H:%M")
        datetimesncf = convert_time(dt)
        
        tabdeparttrain = []
        nexttrain = []
        u=0
        
        nexttrain = Next_train(town1,town2,datetimesncf)
        
        if nexttrain == "error":
            tabdeparttrain.append("Aucun train trouvé ou disponible")
        else :
            for train in nexttrain:
                u = u+1
                deptrain = convertir_str(train)
                tabdeparttrain.append("Train numero "+str(u)+", départ le: "+str(deptrain))
        
        return render_template("result.html", result=round(distance,2), prix=round(prixtrajet['prix'],2), devise=devise, tableau=tabdeparttrain)

def List_Gare() :
    token_auth = '5e044075-940e-4989-87ba-202e60af9e75'

    api_get_gare = requests.get('https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs?', auth=(token_auth, '')).json()
   
    
    if 'error' in api_get_gare:
        tabgare="error"
    else:
        tabgare = []
        n = len(api_get_gare['records'])
        if n > 0:
            for i in range(0, n):
                tabgare.append(tabgare['records'][i]['fields']['gare_alias_libelle_noncontraint'])
       
    return(tabgare)
    
    
def Calcul_distance(town1,town2) :
    url_town1 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q=' + town1
    url_town2 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q=' + town2

    api_town1 = requests.get(url_town1).json()
    api_town2 = requests.get(url_town2).json()
    
    lat_town1 = api_town1['records'][0]['fields']['wgs_84'][0]
    long_town1 = api_town1['records'][0]['fields']['wgs_84'][1]
    
    lat_town2 = api_town2['records'][0]['fields']['wgs_84'][0]
    long_town2 = api_town2['records'][0]['fields']['wgs_84'][1]
    
    client = Client('https://trouve-ton-train-java-soap.herokuapp.com/services/TchouTchou?wsdl')
    result = client.service.calculDistance(long_town1, long_town2, lat_town1, lat_town2)
    return(result)
    
def Next_train(town1,town2,datetimesncf) :
    token_auth = '5e044075-940e-4989-87ba-202e60af9e75'
    #token_auth = keyring.get_password("sncf", "ensae_teaching_cs,key")
    #https://api.sncf.com/v1/coverage/sncf/journeys?from=stop_area:OCE:SA:87746008&to=stop_area:OCE:SA:87722025&datetime=20200317T112327&key=%275e044075-940e-4989-87ba-202e60af9e75a%27
    url_town1 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q="' + town1+'"'
    url_town2 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q="' + town2+'"'
    api_town1 = requests.get(url_town1).json()
    api_town2 = requests.get(url_town2).json()
    UIC1 = api_town1['records'][0]['fields']['pltf_uic_code']
    UIC2 = api_town2['records'][0]['fields']['pltf_uic_code']

    payload = {'from': 'stop_area:OCE:SA:'+str(UIC1), 'to': 'stop_area:OCE:SA:'+str(UIC2), 'min_nb_journeys': 5, 'datetime': datetimesncf}
    api_get_train = requests.get('https://api.sncf.com/v1/coverage/sncf/journeys?', params=payload, auth=(token_auth, '')).json()
    
    

    if 'error' in api_get_train:
        tabtrain="error"
    else:
        tabtrain = []
        n = len(api_get_train['journeys'])
        if n > 0:
            for i in range(0, n):
                tabtrain.append(api_get_train['journeys'][i]['departure_date_time'])
       
    return(tabtrain)

def convert_time(dt) :
    ''' on convertit en chaîne de caractères un datetime'''
    return datetime.strftime(dt, '%Y%m%dT%H%M%S')

def convertir_str(chaine) :
    ''' on convertit en date la chaine de caractères de l API'''
    return datetime.strptime(chaine.replace('T',''),'%Y%m%d%H%M%S')
    
#app.run(debug='true')