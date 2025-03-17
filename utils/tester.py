import requests
import random
import time

online = True

url = "https://jeiquarta.pythonanywhere.com/inserimento" if online else "http://localhost:5000/inserimento"

jollato = [False for _ in range(20)]

def send(id):
    cs = random.randint(1, 20)
    np = random.randint(1, 15)
    res = np if jollato[cs-1] else -1
    chois = random.randint(0, 9)
    if chois > 4:
        res = random.randint(0, 9999)
    elif chois > 0:
        res = np
    else:
        jollato[cs-1] = True
    print(f"{id}: sending request {cs} {np} {res}")
    req = requests.post(url, data = {"codice_squadra": str(cs), "numero_problema": str(np), "risultato": str(res)})
    print("OK" if req.ok else "PROBLEM")
    print()

for id in range(1, 1001):
    send(id)
    time.sleep(1)
