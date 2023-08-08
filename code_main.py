from ecran import Ui_Form

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QImage,QPixmap,QIcon
from PyQt5.QtWidgets import QDialog,QApplication
from PyQt5.uic import loadUi
import cv2
import time
from playsound import playsound
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime

class EcranWindow(QtWidgets.QWidget,Ui_Form):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedWidth(795)
        self.setFixedHeight(590)
        self.setWindowIcon(QtGui.QIcon("security-camera.png"))
        self.ui.afficher.clicked.connect(self.affichage)
        self.ui.arreter.clicked.connect(self.fermer)

    def affichage(self):

        #Lire la vidéo
        cap = cv2.VideoCapture('Chute1.MP4')

        #récupérer les dimension de la vidéo
        vh = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        vl = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        print(" Hauteur : " + str(vh))
        print(" Largeur : " + str(vl))
        print(" Le sol : ")

        # soustraction d'image du fond
        fgbg = cv2.createBackgroundSubtractorMOG2(history=9000, varThreshold=100, detectShadows=True)

        j = 0
        sol = 0

        chute = False

        # Boucle pour lire la video Frame by Frame
        while (1):
            ret, frame1 = cap.read()

            ret, frame2 = cap.read()

            # Convertir chaque frame en N&B pour faciliter la soustraction de l'arriere plan
            try:
                gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)

                fgmask = fgbg.apply(gray)
                self.displayimage1(fgmask, 1,2)


                fgmask = cv2.blur(fgmask,(5,5))
                fgmask = cv2.GaussianBlur(fgmask, (5, 5), 2)

                self.displayimage1(fgmask, 1 , 3)




                # Trouver les contours
                contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:

                    # Une liste pour contenir toutes les régions(zones)
                    areas = []

                    for contour in contours:
                        # Calculer la surface du contour
                        ar = cv2.contourArea(contour)

                        # Ajouter la surface calculée a la fin de la liste
                        areas.append(ar)

                    # Définir la surface la plus grande
                    max_area = max(areas, default=0)

                    # Récuperer l'indice de cette surface
                    max_area_index = areas.index(max_area)

                    cnt = contours[max_area_index]

                    # Moments est une fonction qui va nous aider a calculer le centre de masse
                    M = cv2.moments(cnt)

                    # recuperer les coordonnes du rectangle tel que (x,y)==> la coordonnée en haut à gauche du rectangle et (w,h)==>largeur et sa hauteur
                    x, y, w, h = cv2.boundingRect(cnt)
                    if (y + h != vh):

                        if (sol < y + h):
                            sol = y + h
                            print(sol)

                    # definir une suface minimal pour dessiner les contours (ne pas detecter un chat par exemple)
                    if cv2.contourArea(cnt) < 5000:
                        continue

                    # Dessiner les contours
                    cv2.drawContours(fgmask, [cnt], 0, (255, 255, 255), 3, maxLevel=0)

                    # detecter la chute si La hauteur du contour < largeur
                    # calculer le nombre de frames ou la chute est detecter afin de generer une alerte si on a arrivé a un certain seuil
                    if h > w:
                        j = 0
                        cv2.putText(frame1, 'MOUVEMENT', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:

                            cx, cy = 0, 0
                        cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)
                    if h < w:
                        j += 1
                        cv2.putText(frame1, '', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75, (255, 255, 255), 1)
                        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 255), 2)

                        # Fonction qui calcul lecentre du masse
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                        else:

                            cx, cy = 0, 0
                        cv2.circle(frame1, (cx, cy), 7, (255, 255, 255), -1)

                    # seuil = 60 (5s) alors on declanche l'aletre
                    if j > 60:



                        if (sol - cy < 80):
                            #ici la hauteur < largeur et la personne est sur terre plus de 5s alors on envoi un email
                            print("== FALL ==")
                            chute = True
                            cv2.putText(frame1, 'CHUTE DETECTEE', (x, y), cv2.FONT_HERSHEY_TRIPLEX, 0.75,
                                        (255, 255, 255), 1)
                            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 0, 255), 2)







                    self.displayimage(frame1, 1 )

                    frame1 = frame2

                    if cv2.waitKey(33) == 27:
                        break
            except Exception as e:
                break
        try:

             if (chute == True):
                 dateTimeNow = datetime.datetime.now()

                 msg = MIMEMultipart()
                 msg['From'] = "youremail@gmail.com"
                 msg['To'] = "sendto@gmail.com"
                 password = "password"
                 msg['Subject'] = "ALERTE"
                 body = "Chute détectée =>  à : 2éme étage.n°17 . Bloc A.  Cité 300 lgt Bab Ezzouar.      Le        " +str(dateTimeNow)
                 msg.attach(MIMEText(body, 'html'))

                 server = smtplib.SMTP('smtp.gmail.com', 587)
                 server.starttls()
                 server.login(msg['From'], password)
                 print("LOGIN success")
                 server.sendmail(msg['From'], msg['To'], msg.as_string())
                 server.quit()
                 print("Email envoyé !")
                 QtWidgets.QMessageBox.information(self,"Information","Email envoyé pour signaler la chute ! ")
        except Exception as e:
            print("erreur : Email non envoyé !")
            QtWidgets.QMessageBox.warning(self,"Attention","Email non envoyé ! La chute n'est pas signalée")




    def displayimage(self, img, window=1 ):

        qformat = QImage.Format_Indexed8
        qformat = QImage.Format_RGB888

        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        self.ui.ecran.setPixmap(QPixmap.fromImage(img))
        self.ui.ecran.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)




    def displayimage1(self, img, window=1, x=1):
        qformat = QImage.Format_Indexed8
        qformat = QImage.Format_Grayscale8

        img = QImage(img, img.shape[1], img.shape[0], qformat)
        img = img.rgbSwapped()
        if(x==2):

             self.ui.ecran_2.setPixmap(QPixmap.fromImage(img))
             self.ui.ecran_2.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        if(x==3):
            self.ui.ecran_3.setPixmap(QPixmap.fromImage(img))
            self.ui.ecran_3.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)


    def fermer(self):
        # QtWidgets.QMessageBox.information(self, "Quitter" ,"Merci d'utiliser notre application ! ")
        ret = QtWidgets.QMessageBox.question(self, "Quitter", "Voulez vous fermer l'application ?")

        if (ret == QtWidgets.QMessageBox.Yes):
            self.ui.cap.release()
            app.exit()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    widget = EcranWindow()
    widget.show()
    app.exec_()