import streamlit as st
import pytesseract
from PIL import Image
import re
import io

# =====================================================================
# CONFIGURATION TESSERACT (Optimisée pour Serveur/Cloud)
# =====================================================================
# On ne force PAS de chemin Windows sur le serveur.
# Si tesseract est dans le PATH (grâce au packages.txt), il sera trouvé automatiquement.
try:
    pytesseract.get_tesseract_version()
except:
    # Option de secours si le PATH n'est pas automatique
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
    .id-card-box {
        background-color: #1a153a;
        border-left: 5px solid #00ffcc;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# FONCTIONS LOGIQUES
# =====================================================================
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
        
        num = re.search(r'\b\d{8,15}\b', l)
        if num and champs["Numéro CNI"] == "Non détecté": champs["Numéro CNI"] = num.group(0)
        
        if "SEXE" in l:
            if "M" in l: champs["Sexe"] = "Masculin"
            elif "F" in l: champs["Sexe"] = "Féminin"
    return champs

# =====================================================================
# INTERFACE PRINCIPALE
# =====================================================================
st.markdown('<h1 class="main-title">OCR de Babacar</h1>', unsafe_allow_html=True)

mode = st.radio("Type de document :", ["Document Standard", "Carte d'Identité (CNI)"], horizontal=True)

if mode == "Carte d'Identité (CNI)":
    st.markdown("### 🪪 Scanner CNI (Recto uniquement)")
    fichier = st.file_uploader("Déposez le recto de la CNI", type=["png", "jpg", "jpeg"])
    if fichier:
        st.image(fichier, width=300)
        if st.button("🚀 SCANNER LA CNI"):
            with st.spinner("Analyse en cours..."):
                img = Image.open(fichier).convert('RGB')
                texte = pytesseract.image_to_string(img, lang='fra')
                donnees = extraire_donnees_cni(texte)
                st.session_state.resultat = texte
                st.session_state.donnees = donnees
                st.success("Données extraites avec succès :")
                st.table(list(donnees.items()))

else:
    st.markdown("### 📄 Document Standard")
    fichier = st.file_uploader("Déposez votre document", type=["png", "jpg", "jpeg", "pdf"])
    if fichier and st.button("🚀 ANALYSER LE DOCUMENT"):
        with st.spinner("Analyse du document..."):
            img = Image.open(fichier).convert('RGB')
            texte = pytesseract.image_to_string(img, lang='fra')
            st.session_state.resultat = texte
            st.text_area("Texte extrait :", value=texte, height=200)

# Exportation
if "resultat" in st.session_state:
    st.download_button(
        "📥 Télécharger les résultats (.txt)", 
        data=st.session_state.resultat, 
        file_name="resultat.txt"
    )