import ujson
import socket
from time import sleep

def parseWeather(bodyJson):
    result = {}
    result["text"] = bodyJson["current"]["condition"]["text"]
    result["localTime"] = bodyJson["location"]["localtime"]
    result["currentTemp"] = str(bodyJson["current"]["temp_c"])
    result["currentFeels"] = str(bodyJson["current"]["feelslike_c"])
    result["currentWind"] = str(bodyJson["current"]["wind_kph"])
    result["currentRain"] = "yes" if bodyJson["forecast"]["forecastday"][0]["day"]["daily_will_it_rain"] == 1 else "no"
    result["currentSnow"] = "yes" if bodyJson["forecast"]["forecastday"][0]["day"]["daily_will_it_snow"] == 1 else "no"
    result["currentMin"] = str(bodyJson["forecast"]["forecastday"][0]["day"]["mintemp_c"])
    result["currentMax"] = str(bodyJson["forecast"]["forecastday"][0]["day"]["maxtemp_c"])
    
    
    result["tomorrowRain"] = "yes" if bodyJson["forecast"]["forecastday"][1]["day"]["daily_will_it_rain"] == 1 else "no"
    result["tomorrowSnow"] = "yes" if bodyJson["forecast"]["forecastday"][1]["day"]["daily_will_it_snow"] == 1 else "no"
    result["tomorrowMin"] = str(bodyJson["forecast"]["forecastday"][1]["day"]["mintemp_c"])
    result["tomorrowMax"] = str(bodyJson["forecast"]["forecastday"][1]["day"]["maxtemp_c"])

    return result

def fetchWeatherData():
    requestPath = b"/v1/forecast.json?key=<key>&q=<city>&days=2&aqi=no&alerts=no"
    requesthost = "api.weatherapi.com"

    s = socket.socket()
    s.settimeout(5)
    addri = socket.getaddrinfo(requesthost, 80)
    addr = addri[0][-1]

    print("Resolved address: ", addr)
    s.connect(addr)

    s.send(b"GET ")
    s.send(requestPath)
    s.send(b" HTTP/1.0\r\nHost: api.weatherapi.com\r\nAccept: application/json\r\nConnection: close\r\n\r\n")
    
    response = ""
    received = True
    stop = False
    first = True
    tmp = b""
    while not stop:
        try:
            tmp = s.recv(256)
        except Exception:
            pass
        print("Received:")
        print(len(tmp))
        print("---")
        if len(tmp) < 256:
            if first:
                response = tmp.decode("UTF-8")
                stop = True
                break
            first = False
            if received:
                received=False
                sleep(0.1)
            else:
                stop = True
        else:
            received = True
        response = response + tmp.decode("UTF-8")
        first = False
                
    bodyDecoded = response.split("\r\n\r\n")[1]
    jsonData = ujson.loads(bodyDecoded)
    
    return parseWeather(jsonData)
