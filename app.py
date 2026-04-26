from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import anthropic, base64, json, os, re
import numpy as np, cv2
from fb_admin import firebase_admin
from auth_routes import init_auth_routes
from projects_routes import init_projects_routes
from storage_routes import init_storage_routes
from dotenv import load_dotenv

load_dotenv()

import pytesseract

if os.getenv('RAILWAY_ENVIRONMENT'):
    # Sur Railway, après l'install via le .toml, tesseract est ici :
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    
    
if os.name == 'nt':
    # Configuration pour Windows (votre local)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    # Configuration pour Railway (Linux)
    # Sous Linux, après installation, il est directement dans le PATH
    pytesseract.pytesseract.tesseract_cmd = 'tesseract'
#pytesseract.pytesseract.tesseract_cmd = r"Tesseract-OCR\tesseract.exe"
app = Flask(__name__, static_folder='static')
CORS(app)
os.makedirs('static/uploads', exist_ok=True)

# ── Palette & NFC rules ───────────────────────────────────────────────────────
ROOM_COLORS = ['#4A90D9','#E8734A','#5CB85C','#9B59B6','#F39C12',
               '#E91E63','#00BCD4','#FF5722','#607D8B','#8BC34A']

NFC_RULES = {
    'salon':         {'label':'Salon / Séjour',    'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':5},{'id':'light_ceiling','name':'Plafonnier LED','icon':'💡','power':40,'amp':0.2,'circuit':'éclairage','qty':1},{'id':'ac_unit','name':'Climatiseur','icon':'❄️','power':2500,'amp':11,'circuit':'dédié','qty':1},{'id':'tv_outlet','name':'Prise TV/RJ45','icon':'📺','power':0,'amp':0,'circuit':'courants faibles','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'},{'id':'cb_16a','name':'Disj. 16A','icon':'⚡','spec':'16A courbe C','type':'cb','amp':16,'color':'#5b8af7'}]},
    'chambre':       {'label':'Chambre',            'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':3},{'id':'light_ceiling','name':'Plafonnier LED','icon':'💡','power':40,'amp':0.2,'circuit':'éclairage','qty':1},{'id':'ac_unit','name':'Climatiseur','icon':'❄️','power':2000,'amp':9,'circuit':'dédié','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'}]},
    'cuisine':       {'label':'Cuisine',            'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':6},{'id':'light_ceiling','name':'Plafonnier LED','icon':'💡','power':60,'amp':0.3,'circuit':'éclairage','qty':2},{'id':'hob','name':'Plaque induction','icon':'🔥','power':7200,'amp':32,'circuit':'dédié cuisson','qty':1},{'id':'dishwasher','name':'Lave-vaisselle','icon':'🫧','power':2200,'amp':10,'circuit':'dédié','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'},{'id':'cb_32a','name':'Disj. 32A','icon':'⚡','spec':'32A courbe C','type':'cb','amp':32,'color':'#5b8af7'}]},
    'salle_de_bain': {'label':'Salle de bain',      'devs':[{'id':'outlet_shaver','name':'Prise rasoir Z2','icon':'🔌','power':20,'amp':0.1,'circuit':'PC Z2','qty':1},{'id':'light_mirror','name':'Hublot miroir','icon':'💡','power':30,'amp':0.2,'circuit':'éclairage','qty':1},{'id':'towel_heater','name':'Sèche-serviettes','icon':'🌡️','power':1000,'amp':4.5,'circuit':'dédié','qty':1},{'id':'vmr','name':'VMC','icon':'💨','power':30,'amp':0.2,'circuit':'VMC','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'},{'id':'rcbo_16','name':'RCBO 16A','icon':'🔒','spec':'16A 30mA','type':'rcbo','amp':16,'color':'#3ecf8e'}]},
    'couloir':       {'label':'Couloir / Entrée',   'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':1},{'id':'light_hall','name':'Applique','icon':'💡','power':20,'amp':0.1,'circuit':'éclairage','qty':1},{'id':'doorbell','name':'Sonnette','icon':'🔔','power':5,'amp':0,'circuit':'courants faibles','qty':1}],'prots':[{'id':'cb_10a','name':'Disj. 10A','icon':'⚡','spec':'10A courbe C','type':'cb','amp':10,'color':'#5b8af7'}]},
    'bureau':        {'label':'Bureau',              'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':4},{'id':'light_ceiling','name':'Plafonnier LED','icon':'💡','power':40,'amp':0.2,'circuit':'éclairage','qty':1},{'id':'rj45','name':'Prise RJ45','icon':'🌐','power':0,'amp':0,'circuit':'courants faibles','qty':2}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'}]},
    'garage':        {'label':'Garage',              'devs':[{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':2},{'id':'light_ceiling','name':'Réglette LED','icon':'💡','power':60,'amp':0.3,'circuit':'éclairage','qty':2},{'id':'ev_charger','name':'Borne IRVE','icon':'⚡','power':7400,'amp':32,'circuit':'dédié IRVE','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'},{'id':'cb_32a','name':'Disj. 32A','icon':'⚡','spec':'32A courbe C','type':'cb','amp':32,'color':'#5b8af7'}]},
    'wc':            {'label':'WC / Toilettes',      'devs':[{'id':'light_ceiling','name':'Plafonnier','icon':'💡','power':15,'amp':0.1,'circuit':'éclairage','qty':1},{'id':'vmr','name':'Extracteur','icon':'💨','power':20,'amp':0.1,'circuit':'VMC','qty':1}],'prots':[{'id':'cb_10a','name':'Disj. 10A','icon':'⚡','spec':'10A courbe C','type':'cb','amp':10,'color':'#5b8af7'}]},
    'buanderie':     {'label':'Buanderie',           'devs':[{'id':'washing','name':'Lave-linge','icon':'👕','power':2200,'amp':10,'circuit':'dédié','qty':1},{'id':'outlet_16a','name':'Prise 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':2},{'id':'light_ceiling','name':'Plafonnier','icon':'💡','power':20,'amp':0.1,'circuit':'éclairage','qty':1}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'}]},
    'terrasse':      {'label':'Terrasse / Deck',     'devs':[{'id':'outlet_16a','name':'Prise ext. 16A','icon':'🔌','power':3680,'amp':16,'circuit':'PC','qty':2},{'id':'light_wall','name':'Applique ext.','icon':'💡','power':20,'amp':0.1,'circuit':'éclairage','qty':2}],'prots':[{'id':'rcd_30','name':'DDR 30mA','icon':'🛡️','spec':'30mA/40A','type':'rcd','amp':40,'color':'#f5a524'}]},
}

DEMO_LAYOUT = [
    {'key':'salon',         'x_pct':5,  'y_pct':5,  'w_pct':38,'h_pct':44},
    {'key':'chambre',       'x_pct':46, 'y_pct':5,  'w_pct':28,'h_pct':44},
    {'key':'cuisine',       'x_pct':5,  'y_pct':52, 'w_pct':26,'h_pct':40},
    {'key':'salle_de_bain', 'x_pct':34, 'y_pct':52, 'w_pct':20,'h_pct':40},
    {'key':'couloir',       'x_pct':57, 'y_pct':52, 'w_pct':16,'h_pct':40},
    {'key':'wc',            'x_pct':76, 'y_pct':5,  'w_pct':16,'h_pct':87},
]

def make_rooms(layout):
    rooms = []
    for i, r in enumerate(layout):
        key  = r.get('key') or r.get('type', 'salon')
        rule = NFC_RULES.get(key, NFC_RULES['salon'])
        rooms.append({
            'id':          f'room_{i}',
            'name':        r.get('name') or rule['label'],
            'type':        key,
            'color':       ROOM_COLORS[i % len(ROOM_COLORS)],
            'x_pct':       float(r['x_pct']),
            'y_pct':       float(r['y_pct']),
            'w_pct':       float(r['w_pct']),
            'h_pct':       float(r['h_pct']),
            'devices':     [dict(d) for d in rule['devs']],
            'protections': [dict(p) for p in rule['prots']],
        })
    return rooms

# ── CV detection helpers ──────────────────────────────────────────────────────
PRIORITY_LABELS = [
    ('master bath',    'salle_de_bain'),
    ('master bedroom', 'chambre'),
    ('bathroom',       'salle_de_bain'),
    ('bath',           'salle_de_bain'),
    ('bedroom',        'chambre'),
    ('master',         'chambre'),
    ('kitchen',        'cuisine'),
    ('living',         'salon'),
    ('dining',         'salon'),
    ('aera',           'salon'),
    ('area',           'salon'),
    ('deck',           'terrasse'),
    ('balcony',        'terrasse'),
    ('patio',          'terrasse'),
    ('terrace',        'terrasse'),
    ('laundry',        'buanderie'),
    ('utility',        'buanderie'),
    ('mech',           'couloir'),
    ('mechanical',     'couloir'),
    ('entry',          'couloir'),
    ('foyer',          'couloir'),
    ('closet',         'couloir'),
    ('hall',           'couloir'),
    ('corridor',       'couloir'),
    ('office',         'bureau'),
    ('study',          'bureau'),
    ('garage',         'garage'),
    ('wc',             'wc'),
    ('toilet',         'wc'),
    ('powder',         'wc'),
    # French
    ('salon',          'salon'),
    ('sejour',         'salon'),
    ('chambre',        'chambre'),
    ('cuisine',        'cuisine'),
    ('buanderie',      'buanderie'),
    ('terrasse',       'terrasse'),
    ('couloir',        'couloir'),
    ('bureau',         'bureau'),
    ('entree',         'couloir'),
    ('placard',        'couloir'),
    ('bain',           'salle_de_bain'),
]

NOISE_TOKENS = {'atl','aera','area','o|--','o|-','|--','o|'}
SKIP_RE = re.compile(r'^[0-9()\'"x.,|\-/\\\\]+$')

def _classify(texts):
    combined = ' '.join(texts).lower()
    for kw, rtype in PRIORITY_LABELS:
        if kw in combined:
            return rtype
    return None

def _pos_fallback(cx, cy, ap):
    if ap > 12:
        if cx < 40: return 'chambre',       'Bedroom'
        if cx > 58: return 'chambre',       'Master Bedroom'
        return          'salon',            'Living / Dining'
    if cy < 40:
        if cx < 35: return 'salle_de_bain', 'Bath'
        if cx < 65: return 'cuisine',       'Kitchen'
        return          'buanderie',        'Laundry'
    if cy > 75:     return 'terrasse',       'Deck'
    if cx > 65:     return 'salle_de_bain', 'Master Bath'
    if ap < 5:      return 'wc',            'WC'
    return              'couloir',          'Closet / Hall'

def detect_rooms_cv(image_bytes: bytes) -> list:
    """
    Local room detection using:
      1. Canny edge detection  → enclosed room regions
      2. Connected components  → one component per room
      3. Tesseract OCR         → read room labels
      4. Priority keyword map  → classify each room type
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return make_rooms(DEMO_LAYOUT)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape

    # 1 · Edge map → room boundaries
    edges     = cv2.Canny(gray, 30, 100)
    edges_fat = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    room_mask = cv2.bitwise_not(edges_fat)

    # Remove image border strip
    b = max(15, min(W, H) // 40)
    room_mask[:b, :] = 0;  room_mask[-b:, :] = 0
    room_mask[:, :b] = 0;  room_mask[:, -b:] = 0

    # 2 · Connected components
    num, lmap, stats, centroids = cv2.connectedComponentsWithStats(room_mask)

    min_area = W * H * 0.015          # < 1.5 % → noise
    max_bbox  = 0.55                  # bbox > 55 % → outer frame, skip

    cands = {}
    for i in range(1, num):
        a = stats[i, cv2.CC_STAT_AREA]
        if a < min_area:
            continue
        x, y = stats[i, cv2.CC_STAT_LEFT],  stats[i, cv2.CC_STAT_TOP]
        w, h = stats[i, cv2.CC_STAT_WIDTH],  stats[i, cv2.CC_STAT_HEIGHT]
        cx, cy = centroids[i]
        if (w * h) / (W * H) > max_bbox:   # outer frame — skip
            continue
        pad = 4
        rx, ry = max(0, x - pad), max(0, y - pad)
        rw, rh = min(W - rx, w + 2*pad), min(H - ry, h + 2*pad)
        cands[i] = {
            'area': a, 'x': rx, 'y': ry, 'w': rw, 'h': rh,
            'cx': cx, 'cy': cy,
            'x_pct':    round(rx / W * 100, 1),
            'y_pct':    round(ry / H * 100, 1),
            'w_pct':    round(rw / W * 100, 1),
            'h_pct':    round(rh / H * 100, 1),
            'cx_pct':   round(cx / W * 100, 1),
            'cy_pct':   round(cy / H * 100, 1),
            'area_pct': round(a  / (W * H) * 100, 1),
            'tokens':   [],
        }

    if not cands:
        return make_rooms(DEMO_LAYOUT)

    valid_ids = set(cands.keys())

    # 3 · OCR — assign each text token to the room component it sits in
    ocr = pytesseract.image_to_data(
        gray, output_type=pytesseract.Output.DICT,
        config='--psm 11 --oem 3'
    )
    for i in range(len(ocr['text'])):
        txt  = ocr['text'][i].strip()
        conf = int(ocr['conf'][i])
        if len(txt) < 3 or conf < 35:
            continue
        tx = max(0, min(W - 1, int(ocr['left'][i] + ocr['width'][i]  / 2)))
        ty = max(0, min(H - 1, int(ocr['top'][i]  + ocr['height'][i] / 2)))
        comp = int(lmap[ty, tx])
        if comp in valid_ids:
            cands[comp]['tokens'].append(txt)
        else:
            # Token sits on a wall edge → assign to nearest room centroid
            nearest = min(valid_ids,
                          key=lambda c: (cands[c]['cx'] - tx)**2 + (cands[c]['cy'] - ty)**2)
            cands[nearest]['tokens'].append(txt)

    # 4 · Classify & build output layout
    layout_out = []
    for r in sorted(cands.values(), key=lambda x: -x['area']):
        texts  = r['tokens']
        rtype  = _classify(texts) or _pos_fallback(r['cx_pct'], r['cy_pct'], r['area_pct'])[0]
        # Build a clean human-readable name
        parts  = [t for t in texts
                  if not SKIP_RE.match(t) and len(t) > 2
                  and t.lower() not in NOISE_TOKENS]
        rname  = ' '.join(parts).strip() or NFC_RULES.get(rtype, NFC_RULES['salon'])['label']
        layout_out.append({
            'key':   rtype,  'name':  rname,
            'x_pct': r['x_pct'], 'y_pct': r['y_pct'],
            'w_pct': r['w_pct'], 'h_pct': r['h_pct'],
        })

    return make_rooms(layout_out) if layout_out else make_rooms(DEMO_LAYOUT)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.logger.debug(f"Serving landing from {static_dir}")
    return send_from_directory(static_dir, 'landing.html')

@app.route('/app')
def app_page():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    app.logger.debug(f"Serving app page from {static_dir}")
    return send_from_directory(static_dir, 'index.html')


@app.route('/api/config')
def api_config():
    """
    Serve Firebase configuration to frontend.
    Only returns public configuration - API keys are OK to expose,
    but serviceAccountKey and other sensitive data stay server-side.
    """
    config = {
        'firebase': {
            'apiKey':            os.environ.get('FIREBASE_API_KEY', ''),
            'authDomain':        os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
            'projectId':         os.environ.get('FIREBASE_PROJECT_ID', ''),
            'storageBucket':     os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
            'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId':             os.environ.get('FIREBASE_APP_ID', ''),
            'measurementId':     os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
        }
    }
    return jsonify(config)


@app.route('/api/status')
def api_status():
    has_key = bool(os.environ.get('ANTHROPIC_API_KEY', ''))
    cv_ok   = True
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        cv_ok = False
    return jsonify({'api_key_configured': has_key, 'cv_available': cv_ok})


@app.route('/api/analyze', methods=['POST'])
def analyze_plan():
    mode = request.form.get('mode', 'cv')

    if 'image' not in request.files or not request.files['image'].filename:
        return jsonify({'rooms': make_rooms(DEMO_LAYOUT), 'demo': True,
                        'status': 'no_image', 'message': 'Aucune image — démo activée.'})

    raw_bytes = request.files['image'].read()
    if not raw_bytes:
        return jsonify({'rooms': make_rooms(DEMO_LAYOUT), 'demo': True,
                        'status': 'empty_file', 'message': 'Fichier vide.'}), 400

    # ── CV mode (local, no API key needed) ────────────────────────────────────
    if mode == 'cv':
        try:
            rooms = detect_rooms_cv(raw_bytes)
            return jsonify({
                'rooms':   rooms,
                'demo':    False,
                'mode':    'cv',
                'status':  'ok',
                'count':   len(rooms),
                'message': f'{len(rooms)} pièces détectées (OpenCV + OCR)'
            })
        except Exception as e:
            return jsonify({'rooms': make_rooms(DEMO_LAYOUT), 'demo': True,
                            'mode': 'cv', 'status': 'cv_error',
                            'message': f'Erreur CV : {e}'}), 500

    # ── AI mode (Claude Vision) ───────────────────────────────────────────────
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return jsonify({'rooms': make_rooms(DEMO_LAYOUT), 'demo': True,
                        'mode': 'ai', 'status': 'no_api_key',
                        'message': 'ANTHROPIC_API_KEY manquante — passez en mode CV.'})

    f   = request.files['image']
    ext = (f.filename.rsplit('.', 1)[-1].lower()) if '.' in f.filename else 'jpeg'
    mt  = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png',
           'gif':'image/gif','webp':'image/webp'}.get(ext, 'image/jpeg')
    b64 = base64.standard_b64encode(raw_bytes).decode('utf-8')

    prompt = (
        "Analyse ce plan d'architecture. Identifie TOUTES les pièces visibles.\n"
        "Retourne UNIQUEMENT un JSON valide (sans markdown) :\n"
        '{"rooms":[{"name":"Salon","type":"salon","x_pct":5,"y_pct":5,"w_pct":40,"h_pct":45}]}\n'
        "- x_pct/y_pct : coin haut-gauche en % (0-100)\n"
        "- w_pct/h_pct : largeur/hauteur en % (0-100)\n"
        "- type : salon|chambre|cuisine|salle_de_bain|couloir|bureau|garage|wc|buanderie|terrasse\n"
        "Réponds UNIQUEMENT avec le JSON."
    )
    try:
        client   = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-opus-4-5', max_tokens=2000,
            messages=[{'role': 'user', 'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': mt, 'data': b64}},
                {'type': 'text',  'text': prompt},
            ]}]
        )
    except anthropic.AuthenticationError:
        return jsonify({'error': 'Clé API invalide.', 'demo': True,
                        'rooms': make_rooms(DEMO_LAYOUT), 'status': 'auth_error'}), 401
    except anthropic.RateLimitError:
        return jsonify({'error': 'Limite API atteinte.', 'demo': True,
                        'rooms': make_rooms(DEMO_LAYOUT), 'status': 'rate_limit'}), 429
    except Exception as e:
        return jsonify({'error': str(e), 'demo': True,
                        'rooms': make_rooms(DEMO_LAYOUT), 'status': 'api_error'}), 500

    raw = response.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```\s*$',       '', raw, flags=re.MULTILINE).strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        return jsonify({'error': f'JSON invalide : {e}', 'demo': True,
                        'rooms': make_rooms(DEMO_LAYOUT), 'status': 'parse_error'}), 500

    detected = data.get('rooms', [])
    if not detected:
        return jsonify({'error': 'Aucune pièce détectée.', 'demo': True,
                        'rooms': make_rooms(DEMO_LAYOUT), 'status': 'no_rooms'})

    rooms = make_rooms([{**r, 'key': r.get('type', 'salon')} for r in detected])
    return jsonify({'rooms': rooms, 'demo': False, 'mode': 'ai',
                    'status': 'ok', 'count': len(rooms)})


if __name__ == '__main__':
    print('=' * 55)
    print(' ElecPlan — OpenCV+OCR local  +  Claude IA')
    print('=' * 55)
    k = os.environ.get('ANTHROPIC_API_KEY', '')
    print(f"  Mode IA  : {'✓ clé présente' if k else '✗ ANTHROPIC_API_KEY manquante'}")
    print(f"  Mode CV  : ✓ OpenCV {cv2.__version__} + Tesseract {pytesseract.get_tesseract_version()}")
    print('=' * 55)
    app.run(debug=True, port=5000)
