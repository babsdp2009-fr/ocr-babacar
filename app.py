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

# =====================================================================
# CONFIGURATION TESSERACT
# =====================================================================
chemin_tesseract_windows = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(chemin_tesseract_windows):
    pytesseract.pytesseract.tesseract_cmd = chemin_tesseract_windows
    os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
else:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

st.set_page_config(page_title="OCR de Babacar", layout="wide")

# =====================================================================
# DESIGN CSS (Le style que tu avais demandé)
# =====================================================================
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c20 0%, #15102a 100%); color: #ffffff; }
    .main-title { 
        font-weight: 800; font-size: 3.2rem; 
        background: linear-gradient(45deg, #ff007f, #7f00ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 5px; 
    }
    .stButton > button {
        background: linear-gradient(45deg, #7f00ff, #ff007f) !important;
        color: white !important; font-weight: bold !important;
        border-radius: 8px !important; padding: 12px 24px !important;
        width: 100%; border: none !important;
    }
    .stTable { color: #00ffcc !important; }
    .css-1544g2n { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# FONCTIONS LOGIQUES
# =====================================================================
def extraire_donnees_cni(texte):
    champs = {"Numéro CNI": "Non détecté", "Nom": "Non détecté", "Prénom(s)": "Non détecté", "Date de Naissance": "Non détecté", "Sexe": "Non détecté"}
    lignes = [l.strip() for l in texte.split('\n') if l.strip()]
    for ligne in lignes:
        l = ligne.upper()
        if "NOM" in l and ":" in l: champs["Nom"] = l.split(":", 1)[1].strip()
        if "PRENOM" in l and ":" in l: champs["Prénom(s)"] = l.split(":", 1)[1].strip()
        dates = re.findall(r'\b\d{2}[/\.-]\d{2}[/\.-]\d{4}\b', l)
        if dates: champs["Date de Naissance"] = dates[0]
        num = re.search(r'\b\d{8,15}\b', l)
        if num and champs["Numéro CNI"] == "Non détecté": champs["Numéro CNI"] = num.group(0)
    return champs

# =====================================================================
# INTERFACE
# =====================================================================
st.markdown('<h1 class="main-title">OCR de Babacar</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#b3b0cb;'>Scanner professionnel de documents</p>", unsafe_allow_html=True)

mode = st.radio("Type de document :", ["Document Standard", "Carte d'Identité (CNI)"], horizontal=True)

if mode == "Carte d'Identité (CNI)":
    st.markdown("### 🪪 Scanner CNI (Recto uniquement)")
    fichier = st.file_uploader("Déposez le recto de la CNI", type=["png", "jpg", "jpeg"])
    if fichier:
        st.image(fichier, width=300)
        if st.button("🚀 SCANNER LA CNI"):
            img = np.array(Image.open(fichier))
            texte = pytesseract.image_to_string(img, lang='fra')
            donnees = extraire_donnees_cni(texte)
            st.success("Données extraites avec succès :")
            st.table(list(donnees.items()))
            st.session_state.resultat = texte

else:
    st.markdown("### 📄 Document Standard")
    fichier = st.file_uploader("Déposez votre document", type=["png", "jpg", "jpeg", "pdf"])
    if fichier and st.button("🚀 ANALYSER LE DOCUMENT"):
        st.write("Analyse en cours...")
        # Ici tu remets ton traitement complet de document standard
        st.session_state.resultat = "Texte extrait du document..."

# Export
if "resultat" in st.session_state:
    st.download_button("📥 Télécharger les résultats (.txt)", data=st.session_state.resultat, file_name="resultat.txt")