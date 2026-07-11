import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

# =====================================================================
# CONFIGURATION TESSERACT
# =====================================================================
try:
    pytesseract.get_tesseract_version()
except:
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# =====================================================================
# DESIGN & CSS
# =====================================================================
st.set_page_config(page_title="OCR de Babacar", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c20 0%, #15102a 100%); color: #ffffff; }
    .main-title { 
        font-weight: 800; font-size: 3.2rem; 
        background: linear-gradient(45deg, #ff007f, #7f00ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 20px; 
    }
    .stButton > button {
        background: linear-gradient(45deg, #7f00ff, #ff007f) !important;
        color: white !important; font-weight: bold !important;
        border-radius: 8px !important; padding: 12px 24px !important;
        width: 100%; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# FONCTIONS LOGIQUES
# =====================================================================
def traiter_image_pour_ocr(image_pil):
    # Conversion PIL vers OpenCV
    img_cv = np.array(image_pil.convert('RGB'))
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    # Passage en noir et blanc (Grayscale)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Amélioration du contraste (Seuillage adaptatif)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return processed

def extraire_donnees_cni(texte):
    lignes = [l.strip() for l in texte.split('\n') if l.strip()]
    champs = {
        "Numéro CNI": "Non détecté", "Nom": "Non détecté", 
        "Prénom(s)": "Non détecté", "Date de Naissance": "Non détecté", "Sexe": "Non détecté"
    }
    for i, ligne in enumerate(lignes):
        l = ligne.upper()
        if "NOM" in l and "SURNAME" in l and i+1 < len(lignes): champs["Nom"] = lignes[i+1].strip()
        if "PRENOM" in l and i+1 < len(lignes): champs["Prénom(s)"] = lignes[i+1].strip()
        if "DATE DE NAISS" in l:
            date_match = re.search(r'\d{2}\s\d{2}\s\d{4}', l)
            if date_match: champs["Date de Naissance"] = date_match.group(0)
        if "DU DOCUMENT" in l and i+1 < len(lignes): champs["Numéro CNI"] = lignes[i+1].strip()
        if "SEXE" in l and i+1 < len(lignes):
            valeur = lignes[i+1].strip()
            if "F" in valeur: champs["Sexe"] = "Féminin"
            elif "M" in valeur: champs["Sexe"] = "Masculin"
    return champs

# =====================================================================
# INTERFACE
# =====================================================================
st.markdown('<h1 class="main-title">OCR de Babacar</h1>', unsafe_allow_html=True)

mode = st.radio("Type de document :", ["Document Standard", "Carte d'Identité (CNI)"], horizontal=True)

if mode == "Carte d'Identité (CNI)":
    fichier = st.file_uploader("Déposez le recto de la CNI", type=["png", "jpg", "jpeg"])
    if fichier:
        st.image(fichier, width=300)
        if st.button("🚀 SCANNER LA CNI"):
            with st.spinner("Analyse en cours..."):
                img_pil = Image.open(fichier)
                img_traitee = traiter_image_pour_ocr(img_pil)
                
                # OCR sur l'image traitée
                texte_brut = pytesseract.image_to_string(img_traitee, lang='fra')
                
                donnees = extraire_donnees_cni(texte_brut)
                st.session_state.resultat = texte_brut
                st.success("Données extraites :")
                st.table(list(donnees.items()))
                
                with st.expander("Voir le texte brut détecté (Debug)"):
                    st.text(texte_brut)

else:
    fichier = st.file_uploader("Déposez votre document", type=["png", "jpg", "jpeg", "pdf"])
    if fichier and st.button("🚀 ANALYSER LE DOCUMENT"):
        img_pil = Image.open(fichier)
        texte = pytesseract.image_to_string(img_pil, lang='fra')
        st.session_state.resultat = texte
        st.text_area("Texte extrait :", value=texte, height=200)

if "resultat" in st.session_state:
    st.download_button("📥 Télécharger les résultats (.txt)", data=st.session_state.resultat, file_name="resultat.txt")