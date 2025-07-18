import re
import json
from js import console

def normalize_title(title):
    """Normalize titles for matching"""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'[’‘]', "'", title)
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def parse_reference(reference_line):
    """Parse reference line into components"""
    if not reference_line:
        return ['Author Not Found', 'Year Not Found', 'Title Not Found']
    
    try:
        year_match = re.search(r'\((\d{4}[a-z]?)\)\.?', reference_line)
        if not year_match:
            return ['Author Not Found', 'Year Not Found', 'Title Not Found']
        
        year = year_match.group(1)
        authors_part = reference_line[:year_match.start()].strip()
        title_part = reference_line[year_match.end():].split('.', 1)[0].strip()
        normalized_title = normalize_title(title_part)
        return [authors_part, year, normalized_title]
    
    except (IndexError, AttributeError):
        return ['Author Not Found', 'Year Not Found', 'Title Not Found']

def get_reference_key(reference_line, bib_database):
    """Find BibTeX key for a reference line"""
    if not reference_line:
        return None
        
    parsed_ref = parse_reference(reference_line)
    if not parsed_ref or len(parsed_ref) < 3:
        return None
        
    target_title = parsed_ref[2]
    
    for entry in bib_database.entries:
        if 'title' not in entry:
            continue
        bib_title = entry['title']
        bib_title = bib_title.replace('{', '').replace('}', '')
        bib_title = normalize_title(bib_title)
        if bib_title == target_title:
            return entry['ID']
    return None

def get_reference_line_by_author_year(references, first_author, year_part):
    """Find reference line by author and year"""
    if not references or not first_author or not year_part:
        return None
        
    for line in references.splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = parse_reference(line)
        if len(parsed) < 2:
            continue
        ref_authors = parsed[0]
        ref_year = parsed[1]
        first_ref_author = ref_authors.split(',')[0].split('&')[0].split(' and ')[0].strip()
        if first_ref_author == first_author and ref_year == year_part:
            return line
    return None

def apa2tex(input_refs, input_tex, bib_text):
    """Convert APA citations to LaTeX format"""
    messages = []
    original_tex = input_tex
    conversion_count = 0  # Track successful conversions
    
    try:
        import bibtexparser
        # ... rest of bibtex setup ...
    except Exception as e:
        messages.append(f"Error parsing BibTeX file: {str(e)}")
        return {"output": original_tex, "messages": messages}

    def process_citation(match):
        nonlocal messages, conversion_count
        try:
            original = match.group(0)
            group_content = match.group(1)

            # Skip if content doesn't look like a citation
            if not re.search(r'\d{4}[a-z]?', group_content):
                return original

            # ... existing citation processing ...
            
            for citation in citations:
                # Skip if doesn't look like a citation
                if not re.search(r',\s*\d{4}[a-z]?$', citation):
                    continue
                    
                # ... process citation ...
                
                if key:
                    keys.append(key)

            if valid and keys:
                conversion_count += 1  # Count successful conversion
                # ... return formatted citation ...
            else:
                return original
        except Exception as e:
            return match.group(0)  # Fail silently

    def process_textual_citation(match):
        nonlocal messages, conversion_count
        try:
            authors_text = match.group(1).replace('\\&', '&').strip()
            year_text = match.group(2)
            
            # ... existing processing ...
            
            if key:
                conversion_count += 1  # Count successful conversion
                return f'\\citet{{{key}}}'
            else:
                return match.group(0)
        except Exception as e:
            return match.group(0)  # Fail silently

    try:
        # ... existing conversion process ...
        
        # Add success message if conversions occurred
        if conversion_count > 0:
            messages.append(f"✅ Successfully converted {conversion_count} citations")
        else:
            messages.append("⚠️ No citations were converted. Please check your input formats")
            
        return {"output": converted_tex, "messages": messages}
    except Exception as e:
        messages.append(f"Conversion error: {str(e)}")
        return {"output": original_tex, "messages": messages}

def main(refs_text, tex_text, bib_text):
    """Main conversion function"""
    try:
        result = apa2tex(refs_text, tex_text, bib_text)
        return (result["output"], json.dumps(result["messages"]))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return (tex_text, json.dumps([f"Critical error: {str(e)}\n{error_trace}"]))
