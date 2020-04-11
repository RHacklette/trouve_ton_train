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

@app.route('/formCalculsimple')
def formCalculsimple():
    return render_template("formCalculsimple.html")

@app.route('/Calculsimple', methods=['GET','POST'])
def Calculsimple():
    if request.method == 'POST':
        result = request.form
        town1 = result['town1']
        town2 = result['town2']
        daydepart = result['daydepart']
        timedepart = result['timedepart']
        devise = result['devise']
        
        uic1 = Get_UIC(town1)
        uic2 = Get_UIC(town2)
        
        distance = Calcul_distance(town1,town2)
        
        http_rest="http://trouve-ton-train-rest.herokuapp.com/CalculPrix"
        response = requests.get( http_rest, params =  {'distance' : float(distance), 'devise' : devise })
        prixtrajet = response.json()
        
        departure=daydepart+" "+timedepart
        dt = datetime.strptime(departure, "%Y-%m-%d %H:%M")
        datetimesncf = convert_time(dt)
        
        nexttrain = Next_train(uic1,uic2,datetimesncf)

        return render_template("result.html", result=round(distance,2), prix=round(prixtrajet['prix'],2), devise=devise, tableau=nexttrain)
    
@app.route('/Calcul', methods=['GET','POST'])
def Calcul():
    if request.method == 'POST':
        result = request.form
        uic1 = result['town1']
        uic2 = result['town2']
        daydepart = result['daydepart']
        timedepart = result['timedepart']
        devise = result['devise']
        
        town1 = Get_Name(uic1)
        town2 = Get_Name(uic2)
        distance = Calcul_distance(town1,town2)
        
        http_rest="http://trouve-ton-train-rest.herokuapp.com/CalculPrix"
        response = requests.get( http_rest, params =  {'distance' : float(distance), 'devise' : devise })
        prixtrajet = response.json()
        
        departure=daydepart+" "+timedepart
        dt = datetime.strptime(departure, "%Y-%m-%d %H:%M")
        datetimesncf = convert_time(dt)
        
        nexttrain = Next_train(uic1,uic2,datetimesncf)

        return render_template("result.html", result=round(distance,2), prix=round(prixtrajet['prix'],2), devise=devise, tableau=nexttrain)

def List_Gare() :
    page_initiale = page_gares(0)
    item_per_page = page_initiale.json()['pagination']['items_per_page']
    total_items = page_initiale.json()['pagination']['total_result']

    new_dict=dict()
    
    for page in range(int(total_items/item_per_page)+1) :
        stations_page = page_gares(page)
    
        ensemble_stations = stations_page.json()
    
        if 'stop_areas' not in ensemble_stations:
            # pas d'arrêt
            continue
    
        # on ne retient que les informations qui nous intéressent
        for station in ensemble_stations['stop_areas']:
    
            if 'administrative_regions' in station.keys() :
                #dfs.append(station['administrative_regions'][0]['name'])
                name = station['administrative_regions'][0]['name']
                uid = station['id']	
                new_dict[name] = uid
        
    return(new_dict)
        
    
def page_gares(numero_page) :
    token_auth = '5e044075-940e-4989-87ba-202e60af9e75'
    return requests.get(('https://api.sncf.com/v1/coverage/sncf/stop_areas?start_page={}').format(numero_page),auth=(token_auth, ''))
    
def Calcul_distance(town1,town2) :
    url_town1 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q="' + town1+'"'
    url_town2 = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q="' + town2+'"'

    api_town1 = requests.get(url_town1).json()
    api_town2 = requests.get(url_town2).json()
    
    lat_town1 = api_town1['records'][0]['fields']['wgs_84'][0]
    long_town1 = api_town1['records'][0]['fields']['wgs_84'][1]
    
    lat_town2 = api_town2['records'][0]['fields']['wgs_84'][0]
    long_town2 = api_town2['records'][0]['fields']['wgs_84'][1]
    
    client = Client('https://trouve-ton-train-java-soap.herokuapp.com/services/TchouTchou?wsdl')
    result = client.service.calculDistance(long_town1, long_town2, lat_town1, lat_town2)
    return(result)
    
def Get_UIC(town):
    url_town = 'https://data.sncf.com/api/records/1.0/search/?dataset=referentiel-gares-voyageurs&q="' + town+'"'
    api_town = requests.get(url_town).json()
    UIC = api_town['records'][0]['fields']['pltf_uic_code']
    #uic = 'stop_area:OCE:SA:'+str(UIC)
    return(UIC)
    
def Get_Name(UIC):
    token_auth = '5e044075-940e-4989-87ba-202e60af9e75'
    url="https://api.sncf.com/v1/coverage/sncf/stop_areas/stop_area:"+UIC
    api_get_name = requests.get(url, auth=(token_auth, '')).json()
    name = api_get_name['stop_areas'][0]['administrative_regions'][0]['name']
    return(name)
    

def Next_train(UIC1,UIC2,datetimesncf) :

    token_auth = '5e044075-940e-4989-87ba-202e60af9e75'
    payload = {'from': str(UIC1), 'to': str(UIC2), 'min_nb_journeys': 5, 'datetime': datetimesncf}
    api_get_train = requests.get('https://api.sncf.com/v1/coverage/sncf/journeys?', params=payload, auth=(token_auth, '')).json()

    tabdeparttrain = []
    if 'error' in api_get_train:
        tabdeparttrain.append("Aucun train trouvé ou disponible")
    else:
        tabtrain = []
        n = len(api_get_train['journeys'])
        if n > 0:
            for i in range(0, n):
                tabtrain.append(api_get_train['journeys'][i]['departure_date_time'])
            
            u=0
            for train in tabtrain:
                u = u+1
                deptrain = convertir_str(train)
                tabdeparttrain.append("Train numero "+str(u)+", départ le: "+str(deptrain))
       
    return(tabdeparttrain)

def convert_time(dt) :
    ''' on convertit en chaîne de caractères un datetime'''
    return datetime.strftime(dt, '%Y%m%dT%H%M%S')

def convertir_str(chaine) :
    ''' on convertit en date la chaine de caractères de l API'''
    return datetime.strptime(chaine.replace('T',''),'%Y%m%d%H%M%S')
    
#app.run(debug='true')