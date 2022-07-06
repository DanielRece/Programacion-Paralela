#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 30 11:25:57 2022
@author: alumno
"""

import matplotlib.pyplot as plt
from pyspark import SparkContext
sc = SparkContext.getOrCreate()
import json
import re
import datetime

VALORES = ['user_day_code','user_type','ageRange','idplug_station',
         'idunplug_station','unplug_hourTime','travel_time']

def adaptar(dicc):
        """
        Desempaqueta las fechas en forma unplug_hourTime: {$date: string}.
        """
    
        if isinstance(dicc['unplug_hourTime'], dict):
            dicc['unplug_hourTime'] = dicc['unplug_hourTime']['$date']
            
        return dicc


def leer(lista):
    """
    Recibe una lista de archivos json, se queda con los datos relevantes, y ajusta el formato de las fechas.
    Devuelve un unico rdd con todos los datos.
    """
    
    if not isinstance(lista, list):
        lista = [lista]
        
    sc = SparkContext.getOrCreate()
    aux = lambda x: {a:x[a] for a in VALORES}
    
    total = sc.textFile(lista[0]).map(json.loads).map(aux)
    
    for archivo in lista[1:]:
        dat = sc.textFile(archivo).map(json.loads).map(aux)
        total = total.union(dat)
    
    return total.map(adaptar)


PATTERN = re.compile(r'[+][0-9]+$')

def tiempo(content):
    """
    Una funcion para transformar string a objeto datetime.
    Las fechas tienen dos formatos distintos y se tratan de la misma forma
    con una expresion regular.
    """
    
    match = PATTERN.search(content)
    if match:
        formato = '%Y-%m-%dT%H:%M:%S.%f%z'  
    else:
        formato = '%Y-%m-%dT%H:%M:%SZ'
        
    return datetime.datetime.strptime(content, formato)

# Prueba de sacar los datos.
a = leer('202001_movements.json').sample(False, 0.2)
print("Sacar 10 elementos del archivo de datos:", a. take(10))


###
a = leer('202001_movements.json')
rdd = a.map(lambda x: (x['user_day_code'],x)).groupByKey().mapValues(list)
numero = rdd.mapValues(len).sortBy(keyfunc=lambda x: x[1],ascending=False)
print("cinco usuarios que más utilizado en un día:", numero.take(5))


###
rdd = a.map(lambda x: (x['user_day_code'],x)).groupByKey().mapValues(list)
ida = rdd.filter(lambda x: x[1][0]['idunplug_station']==x[1][-1]['idplug_station'])
print("porcentaje de personas que comienzan y acaban en la misma estacion: ",100*ida.count()/rdd.count())


###
def condicion(lista):
    
    b = True
    j = 1
    while j < len(lista):
        b = b and lista[j-1]['idunplug_station'] == lista[j]['idplug_station']
        j += 1
    return b    

temp = rdd.filter(lambda x: len(x[1])>2).filter(lambda x: condicion(x[1]))
print("Cinco viaje sucesivo empieza en la estacion donde acabo el viaje previo.", temp.take(5))


###
rdd = a.map(lambda x: (x['user_type'],x)).groupByKey().mapValues(len)
print("número de viajes según los abonos", rdd.collect())


###
rdd = a.map(lambda x: x['travel_time'])
print('Conteo:',rdd.filter(lambda x: x>120).count())
print('Media:',rdd.filter(lambda x: x>120).mean())


###
rdd = a.flatMap(lambda x: [x['idunplug_station'],x['idplug_station']])
b=rdd.countByValue()#.sortBy(keyfunc=id,ascending=False)
print("diccionario con estaciones más utilizadas ordenada de forma descendente", dict(sorted(b.items(), key=lambda item: item[1],reverse=True)))


###
rdd = a.map(lambda x: x['idplug_station'])
b=rdd.countByValue()#.sortBy(keyfunc=id,ascending=False)
print("Estaciones con más gente que lllegan", dict(sorted(b.items(), key=lambda item: item[1],reverse=True)))


###
datos=leer(['201706_Usage_Bicimad.json','201707_Usage_Bicimad.json','201708_Usage_Bicimad.json','201709_Usage_Bicimad.json','201711_Usage_Bicimad.json','201712_Usage_Bicimad.json','201801_Usage_Bicimad.json','201802_Usage_Bicimad.json'])
datos=datos.map(lambda x: tiempo(x['unplug_hourTime']))
datos_verano = datos.filter(lambda x: 9>=x.month>=6)
datos_invierno = datos.filter(lambda x: 11>=x.month or x.month<=2)
a=datos_verano.count()
b=datos_invierno.count()
print("número de usuarios que usan en verano e invierno y la proporcion de ellos:",a,b,a/b)


### Histograma respecto de tipo de usuarios
l_rdd=['201706_Usage_Bicimad.json','201707_Usage_Bicimad.json','201708_Usage_Bicimad.json','201709_Usage_Bicimad.json','201711_Usage_Bicimad.json','201712_Usage_Bicimad.json','201801_Usage_Bicimad.json','201802_Usage_Bicimad.json']
plt.rcParams["figure.figsize"] = (12,12)
fig = plt.figure()
j = 1
for t in l_rdd:
    datos = leer(t).map(lambda x: x['user_type']).countByValue()
    st = f'axfig_{j}'
    st = fig.add_subplot(3,4,j)
    st.title.set_text(t)
    plt.bar(datos.keys(),datos.values())
    j += 1
    
    
### Histograma respecto de rango de edades
plt.rcParams["figure.figsize"] = (12,12)
fig = plt.figure()
j = 1
for t in l_rdd:
    datos = leer(t).map(lambda x: x['ageRange']).countByValue()
    st = f'axfig_{j}'
    st = fig.add_subplot(3,4,j)
    st.title.set_text(t)
    plt.bar(datos.keys(),datos.values())  
    j += 1



