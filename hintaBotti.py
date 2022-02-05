import requests
from bs4 import BeautifulSoup
import csv
import imaplib
import email
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

username = 'hintaseurantabotti@gmail.com'
password = 'XXX'

def lue_sposti():
    maili = imaplib.IMAP4_SSL('imap.gmail.com')
    maili.login(username, password)
    maili.select("inbox")
    _, search_data = maili.search(None, 'UNSEEN')
    kaikkiSpostitListana = []
    for num in search_data[0].split(): #Käy läpi kaikki avaamattomat spostit ja lisää email_data-sanakirjan spostilistaan
        email_data = {}
        _, data = maili.fetch(num, '(RFC822)')
        _, b = data[0]
        email_message = email.message_from_bytes(b)

        for header in ['subject', 'from']:
            email_data[header] = email_message[header]

        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
                email_data['body'] = body.decode()

        kaikkiSpostitListana.append(email_data) 
    

    for i in kaikkiSpostitListana: #Testaa onko spostin otsikko ja tekstisisältö kelvollinen, jos on lisätään CSV-tiedostoon 
        try:                       #spostin sisältö eli URL;haluttu hinta;lähettäjä
            if testaa_sposti_sisalto(i["subject"], i["body"].strip()) == True:
                haluttuHinta = int(i["subject"])
                lahettaja = i["from"]
                lahettaja = lahettaja.split("<")
                lahettaja = lahettaja[1][:-1]
                urli = i["body"].strip() #Turhat välilyönnit urlin perästä pois
                b = [urli, str(haluttuHinta), lahettaja]
                rimpsu = ";".join(b)
                with open("asiakastiedot.csv", "a") as tiedosto:
                    print("CSV kirjotus", rimpsu)
                    tiedosto.write(f"{rimpsu}\n")
            else:
                print("EI MENNYT SPOSTITARKASTUS LAPI!")
        except:
            continue


def laheta_sposti(text='Email Body', subject='Hintaseuranta botin automaattinen sposti!', from_email='Botti Bottinen <hintaseurantabotti@gmail.com>', to_emails=None):
    assert isinstance(to_emails, list)
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = subject

    txt_part = MIMEText(text, 'plain')
    msg.attach(txt_part)

    msg_str = msg.as_string()
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(from_email, to_emails, msg_str)
    server.quit()


def testaa_sposti_sisalto(subjekti, body):
    try:
        a = int(subjekti) #Jos otsikkoa ei voida muuttaa int-muotoon palautetaan false
        b = body.split()
        if len(b) != 1: #Jos tekstisisältö sisältää välilyöntejä ei se ole sääntöjen vastainen, palautetaan false
            return False
        if "verkkokauppa.com" not in body:
            if "gigantti.fi" not in body:
                if "xxl.fi" not in body:
                    return False
    except:
        return False
    return True

def palauta_stripattu_arvo(hinta):        # Turhien välilöyntien/merkkien poistaminen
    intLista = []                   
    for x in hinta:
        try: 
            a = int(x)
            intLista.append(x)
        except:
            continue
    numerot = "".join(intLista)
    return numerot
    

def lueSivu_ja_palautaHinta(URL):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36"}
    try:
        page = requests.get(URL, headers=headers) # Vielä yksi varmistus ettei requestata väärä urlia ja looppi kaatuisi siihen
    except: 
        return None
    soup = BeautifulSoup(page.content, "html.parser")

    # Eri verkkosivujen koodirakenne on tietenkin erinlaista, joten jotta saadaan haravoitua hinta on omakin koodi oltava eri
    if "verkkokauppa.com" in URL:
        sivunSisalto = soup.find_all("data", class_="CurrentData-sc-1eckydb-0 hwBNUf")
        for i in sivunSisalto:
            for j in i:
                hintaSivulla = int(palauta_stripattu_arvo(j))
                return (hintaSivulla, "Ei speciaalia")

    elif "xxl.fi" in URL:
        sivunSisalto = soup.find_all("div", class_="product__price")
        b = 0
        for i in sivunSisalto:
            for j in i:      
                for a in j:
                    if b == 1:
                        hinta = a[:-1]
                        hintaSplitattu = hinta.split(",")
                        hintaSivulla = int(palauta_stripattu_arvo(hintaSplitattu[0]))
                        return (hintaSivulla, "Ei Speciaalia")
                    b = b + 1


    elif "gigantti.fi" in URL:
        sivunSisalto = soup.find_all("div", class_="product-price-container")
        klubiAlennusSisalto = soup.find_all("span", class_="sales-point")
        if len(klubiAlennusSisalto) == 0:
            klubiAlennusSisalto.append(" ")
        if "KLUBITARJOUS" in str(klubiAlennusSisalto[0]):   # Joissain tilanteissa alennettu hinta ei ole "normaalilla" paikalla vaan
            for i in klubiAlennusSisalto:                   # klubitarjouksena eri kentässä joten se joudutaan käymään joka kerta läpi
                for j in i:                                 # Tarjous tagin kohdalla voi myös olla muuta, kuten "Kampanjahintaan!"
                    splitattuKlubiTarjous = j.split()
                    klubiHinta = splitattuKlubiTarjous[1] 
                    if "," in klubiHinta:      
                        pilkullaSplitattu = klubiHinta.split(",")
                        klubiHinta = int(palauta_stripattu_arvo(pilkullaSplitattu[0]))
                    else:
                        klubiHinta = int(palauta_stripattu_arvo(klubiHinta[:-1])) # Poistetaan € merkki lopusta
                    break
                break
    

        b = 0
        for i in sivunSisalto:
            for j in i:
                for a in j:
                    continue
                else:
                    if b == 1:
                        desimaaliEkaOsa = a.split(",")
                        hintaSivulla = int(palauta_stripattu_arvo(desimaaliEkaOsa[0]))
                        
                        try:
                            if int(klubiHinta) <= int(hintaSivulla):
                                return (klubiHinta, "klubi")      # Palautetaan parametrina myös "klubi", jotta voidaan kertoa spostissa se
                            return (hintaSivulla, "Ei speciaalia")
                        except:
                            return (hintaSivulla, "Ei speciaalia")
                    b = b + 1

def paivita_csv(paivitettyTaulu):    # Jos asiakkaalle on lähetetty sposti hinnan alenemisesta poistetaan se tilauslistalta
    with open("asiakastiedot.csv", "w") as tiedosto:
        for i in paivitettyTaulu:
            a = ";".join(i)
            tiedosto.write(f"{a}\n")
            

def lue_csv():  # Lukee CSV:n rivi kerralla ja kutsuu hinnan palauttavaa funktiota. Jos toivottu hinta alittuu lähetetään sposti asiakkaalle
    paivitettyTaulu = []
    with open("asiakastiedot.csv", "r") as tiedosto:
        for rivi in csv.reader(tiedosto, delimiter=";"):             
            hintaSivulla = lueSivu_ja_palautaHinta(rivi[0])
            print("HINTASIVULLA FUNKTIO PALAUTTI ARVON:", hintaSivulla)
            if hintaSivulla != None:
                if type(hintaSivulla[0]) == int:
                    if int(rivi[1]) >= hintaSivulla[0]:
                        print("SPOSTI LAHETYS!", hintaSivulla[0], rivi[1])   
                        if hintaSivulla[1] == "klubi":  # Erillinen sposti jos kyseessä on klubitarjous
                        
                            laheta_sposti(text=f"Hei!\n\nHintaseurannassa olleen tuotteen {rivi[0]} hinta on alittanut haluamanne {rivi[1]} euroa!\n\nTuotteen hinta on nyt {hintaSivulla[0]} euroa.\n\nHuomaathan, että kyseessä on Gigantin klubitarjous!", to_emails=[rivi[2]])
                        else:
                            laheta_sposti(text=f"Hei!\n\nHintaseurannassa olleen tuotteen {rivi[0]} hinta on alittanut haluamanne {rivi[1]} euroa!\n\nTuotteen hinta on nyt {hintaSivulla[0]} euroa.", to_emails=[rivi[2]])
                        
                    else:
                        paivitettyTaulu.append(rivi) # Jos hinta ei alitu säilytetään se tiedostossa
                        print(f"EI ALITTUNUT HINTA! Hintasivulla: {hintaSivulla[0]} haluttu hinta: {rivi[1]}")
                else:
                    continue
            else:
                continue
                
            time.sleep(2)
    paivita_csv(paivitettyTaulu)
    

def main():
    lue_sposti()
    lue_csv()

main()
