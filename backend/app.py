from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
import io
import re

app = Flask(__name__)
CORS(app)  # needed for frontend to call backend

def normalize_text(text):
    # make everything lowercase and remove extra spaces for comparison
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())

def find_percentage(text):
    # find numbers with % sign
    matches = re.findall(r'(\d+\.?\d*)\s*%', text.lower())
    percentages = []
    for match in matches:
        try:
            val = float(match)
            if 0 <= val <= 100:  # reasonable range
                percentages.append(val)
        except:
            pass
    return percentages

def find_volume(text):
    # look for volume patterns like "750 mL" or "12 fl oz"
    patterns = [
        r'(\d+\.?\d*)\s*(ml|mL)',
        r'(\d+\.?\d*)\s*(fl\s*oz|oz)',
        r'(\d+\.?\d*)\s*(l|L)',
    ]
    volumes = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            if isinstance(match, tuple):
                volumes.append(f"{match[0]} {match[1]}".strip())
    return volumes

def check_match(label_text, form_value, field_name):
    if not form_value:
        return False, f"{field_name} not provided in form"
    
    label_lower = normalize_text(label_text)
    form_lower = normalize_text(form_value)
    
    # exact match
    if form_lower in label_lower:
        return True, f"{field_name} found on label"
    
    # partial match for multi-word fields (OCR might miss a word)
    form_words = form_lower.split()
    if len(form_words) > 1:
        found = sum(1 for word in form_words if word in label_lower)
        if found >= len(form_words) * 0.7:  # 70% of words match
            return True, f"{field_name} partially matched"
    
    return False, f"{field_name} not found on label"

def check_alcohol(label_text, form_abv):
    if not form_abv:
        return False, "Alcohol content not provided"
    
    # parse form value (handle "45%" or just "45")
    try:
        form_value = float(re.sub(r'[%\s]', '', form_abv))
    except:
        return False, f"Invalid alcohol content: {form_abv}"
    
    label_percentages = find_percentage(label_text)
    if not label_percentages:
        return False, f"Alcohol content not found on label (expected {form_value}%)"
    
    # check if any percentage matches (with small tolerance for OCR errors)
    for label_val in label_percentages:
        if abs(label_val - form_value) <= 0.5:
            return True, f"Alcohol content matches: {label_val}%"
    
    return False, f"Alcohol content mismatch: found {label_percentages[0]}%, expected {form_value}%"

def check_volume(label_text, form_volume):
    if not form_volume:
        return True, "Net contents not required"  # optional field
    
    label_volumes = find_volume(label_text)
    if not label_volumes:
        return False, f"Net contents not found on label (expected {form_volume})"
    
    form_lower = normalize_text(form_volume)
    for label_vol in label_volumes:
        # check both ways in case formatting differs
        if form_lower in normalize_text(label_vol) or normalize_text(label_vol) in form_lower:
            return True, f"Net contents matches: {label_vol}"
    
    return False, f"Net contents mismatch: found {label_volumes[0]}, expected {form_volume}"

def check_warning(label_text):
    text_lower = normalize_text(label_text)
    if "government warning" in text_lower:
        return True, "Government warning found on label"
    
    # check for key phrases (OCR might not get exact text)
    phrases = ["pregnant", "driving", "operating machinery", "health problems"]
    found = [p for p in phrases if p in text_lower]
    if len(found) >= 2:
        return True, "Government warning partially found"
    
    return False, "Government warning not found on label"

@app.route('/api/verify', methods=['POST'])
def verify_label():
    try:
        form_data = request.form.to_dict()
        
        # check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # read image and run OCR
        image = Image.open(io.BytesIO(image_file.read()))
        try:
            extracted_text = pytesseract.image_to_string(image)
        except Exception as e:
            return jsonify({'error': 'Failed to process image', 'details': str(e)}), 500
        
        # check if OCR got anything useful
        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({
                'error': 'Could not read text from image. Please try a clearer image.'
            }), 400
        
        # build results object
        results = {
            'overall_match': True,
            'extracted_text_preview': extracted_text[:200] + '...' if len(extracted_text) > 200 else extracted_text,
            'checks': []
        }
        
        # run all the checks
        brand_match, brand_msg = check_match(extracted_text, form_data.get('brandName', ''), 'Brand Name')
        results['checks'].append({'field': 'Brand Name', 'matched': brand_match, 'message': brand_msg})
        if not brand_match:
            results['overall_match'] = False
        
        class_match, class_msg = check_match(extracted_text, form_data.get('productClass', ''), 'Product Class/Type')
        results['checks'].append({'field': 'Product Class/Type', 'matched': class_match, 'message': class_msg})
        if not class_match:
            results['overall_match'] = False
        
        abv_match, abv_msg = check_alcohol(extracted_text, form_data.get('alcoholContent', ''))
        results['checks'].append({'field': 'Alcohol Content', 'matched': abv_match, 'message': abv_msg})
        if not abv_match:
            results['overall_match'] = False
        
        # net contents is optional
        if form_data.get('netContents'):
            vol_match, vol_msg = check_volume(extracted_text, form_data.get('netContents', ''))
            results['checks'].append({'field': 'Net Contents', 'matched': vol_match, 'message': vol_msg})
            if not vol_match:
                results['overall_match'] = False
        
        warning_match, warning_msg = check_warning(extracted_text)
        results['checks'].append({'field': 'Government Warning', 'matched': warning_match, 'message': warning_msg})
        if not warning_match:
            results['overall_match'] = False
        
        return jsonify(results), 200
        
    except Exception as e:
        # catch-all for any other errors
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # using 5001 because 5000 is used by AirPlay on Mac
    app.run(debug=True, port=5001, host='0.0.0.0')
