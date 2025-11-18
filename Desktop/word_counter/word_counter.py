from flask import Flask, render_template, request, jsonify
import os
from collections import Counter
import re

app = Flask(__name__)

# Configure upload folders
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'text'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def count_words(text):
    """
    Count words in text and provide detailed statistics
    Returns: dictionary with word count and statistics
    """
    # Remove extra whitespace and split into words
    words = text.split()
    
    # Count total words
    word_count = len(words)
    
    # Count characters (excluding spaces)
    char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    
    # Count characters (including spaces)
    char_count_with_spaces = len(text)
    
    # Count lines
    lines = text.split('\n')
    line_count = len(lines)
    
    # Count sentences (approximate)
    sentence_count = len(re.findall(r'[.!?]+', text))
    
    # Count paragraphs (separated by blank lines)
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    paragraph_count = len(paragraphs)
    
    # Find most common words (case-insensitive)
    # Remove punctuation for accurate word counting
    clean_words = re.findall(r'\b\w+\b', text.lower())
    word_frequency = Counter(clean_words)
    most_common = word_frequency.most_common(10)
    
    # Calculate average word length
    if clean_words:
        avg_word_length = sum(len(word) for word in clean_words) / len(clean_words)
    else:
        avg_word_length = 0
    
    return {
        'word_count': word_count,
        'char_count': char_count,
        'char_count_with_spaces': char_count_with_spaces,
        'line_count': line_count,
        'sentence_count': sentence_count if sentence_count > 0 else 1,
        'paragraph_count': paragraph_count if paragraph_count > 0 else 1,
        'most_common_words': most_common,
        'avg_word_length': round(avg_word_length, 2),
        'unique_words': len(word_frequency)
    }

def read_file(filepath):
    """
    Read content from a file with exception handling
    Returns: tuple (success, content/error_message)
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            return False, "Error: File not found"
        
        # Check if it's a file (not a directory)
        if not os.path.isfile(filepath):
            return False, "Error: Path is not a file"
        
        # Try to read the file
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if file is empty
        if not content.strip():
            return False, "Error: File is empty"
        
        return True, content
    
    except FileNotFoundError:
        return False, "Error: File not found"
    except PermissionError:
        return False, "Error: Permission denied to read file"
    except UnicodeDecodeError:
        return False, "Error: File encoding not supported (use UTF-8 text files)"
    except Exception as e:
        return False, f"Error: {str(e)}"

@app.route('/')
def index():
    """Serve the word counter HTML page"""
    return render_template('word_counter.html')

@app.route('/count_file', methods=['POST'])
def count_file():
    """Count words from uploaded file"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only .txt files are allowed'}), 400
        
        # Save file temporarily
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Read and count words
        success, content = read_file(filepath)
        
        # Remove temporary file
        try:
            os.remove(filepath)
        except:
            pass
        
        if not success:
            return jsonify({'error': content}), 400
        
        # Count words and get statistics
        stats = count_words(content)
        stats['filename'] = file.filename
        stats['preview'] = content[:500]  # First 500 characters
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/count_text', methods=['POST'])
def count_text():
    """Count words from text input"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Please enter some text'}), 400
        
        # Count words and get statistics
        stats = count_words(text)
        stats['preview'] = text[:500]
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': f'Error processing text: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

