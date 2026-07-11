import os
import re
import cv2
import io
import numpy as np
import streamlit as st
from PIL import Image
import pytesseract
from docx import Document  
from fpdf import FPDF  

# --- CONFIGURATION ---
chemin_tesseract_windows = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(chemin_tesseract_windows):
    pytesseract.pytesseract.tesseract_cmd = chemin_tesseract_windows
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
else:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(page_title="Scanner Pro", layout="wide")

# --- FONCTION D'EXTRACTION CNI (Analyse de texte) ---
def extraire_donnees_cni(texte):
    champs = {
        "Numéro CNI": "Non détecté",
        "Nom": "Non détecté",
        "Prénom(s)": "Non détecté",
        "Date de Naissance": "Non détecté",
        "Sexe": "Non détecté"
    }
    lignes = [l.strip() for l in texte.split('\n') if l.strip()]
    for ligne in lignes:
        l = ligne.upper()
        if "NOM" in l and ":" in l: champs["Nom"] = l.split(":", 1)[1].strip()
        if "PRENOM" in l and ":" in l: champs["Prénom(s)"] = l.split(":", 1)[1].strip()
        dates = re.findall(r'\b\d{2}[/\.-]\d{2}[/\.-]\d{4}\b', l)
        if dates: champs["Date de Naissance"] = dates[0]
        # Recherche d'un numéro d'identification (série de chiffres)
        num = re.search(r'\b\d{8,15}\b', l)
        if num and champs["Numéro CNI"] == "Non détecté": champs["Numéro CNI"] = num.group(0)
        if "SEXE" in l:
            if "M" in l: champs["Sexe"] = "Masculin"
            elif "F" in l: champs["Sexe"] = "Féminin"
    return champs

# --- INTERFACE ---
st.title("OCR Intelligent")

# Choix du mode
mode = st.radio("Quel type de document souhaitez-vous scanner ?", ["Document Standard", "Carte d'Identité (CNI)"], horizontal=True)

if mode == "Carte d'Identité (CNI)":
    st.info("ℹ️ Veuillez déposer uniquement le **recto** de votre CNI.")
    fichier = st.file_uploader("Déposer le recto de la CNI", type=["png", "jpg", "jpeg"])
    
    if fichier:
        st.image(fichier, width=400)
        if st.button("Scanner la CNI"):
            img = np.array(Image.open(fichier))
            texte = pytesseract.image_to_string(img, lang='fra')
            donnees = extraire_donnees_cni(texte)
            
            st.success("Données extraites :")
            st.table(list(donnees.items()))
            st.session_state.texte_final = texte

else:
    st.info("ℹ️ Vous pouvez déposer tout type de document (PDF, Image, Word).")
    fichier = st.file_uploader("Déposer le document", type=["png", "jpg", "jpeg", "pdf"])
    if fichier and st.button("Scanner le document"):
        # Logique de ton ancien code pour documents standards ici
        st.write("Analyse du document standard en cours...")

# Exportation (si des données existent)
if "texte_final" in st.session_state:
    if st.download_button("Télécharger les résultats (.txt)", data=st.session_state.texte_final, file_name="resultat.txt"):
        st.balloons()