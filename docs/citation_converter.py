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
    conversion_count = 0
    
    try:
        import bibtexparser
        from bibtexparser.bibdatabase import BibDatabase
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = bibtexparser.loads(bib_text, parser=parser)
    except Exception as e:
        messages.append(f"Error parsing BibTeX file: {str(e)}")
        return {"output": original_tex, "messages": messages}

    def normalize_author(author_str):
        """Normalize author names for matching, preserving LaTeX escapes"""
        if not author_str:
            return ""
        # Replace LaTeX escaped ampersands with plain ampersands
        author_str = author_str.replace('\\&', '&')
        author_str = author_str.lower()
        # Remove special characters except spaces and ampersands
        author_str = re.sub(r'[^a-z\s&]', '', author_str)
        author_str = re.sub(r'\s+', ' ', author_str).strip()
        return author_str

    def parse_reference(reference_line):
        """Parse reference line into components with LaTeX handling"""
        if not reference_line:
            return ['Author Not Found', 'Year Not Found', 'Title Not Found']
        
        try:
            # Handle LaTeX escaped ampersands in references
            reference_line = reference_line.replace('\\&', '&')
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
            # Clean LaTeX formatting
            bib_title = bib_title.replace('{', '').replace('}', '')
            bib_title = normalize_title(bib_title)
            if bib_title == target_title:
                return entry['ID']
        return None

    def get_reference_line_by_author_year(references, target_author, year_part):
        """Find reference line by author and year with flexible matching"""
        if not references or not target_author or not year_part:
            return None
            
        # Normalize target author
        target_author = normalize_author(target_author)
        
        for line in references.splitlines():
            line = line.strip()
            if not line:
                continue
                
            parsed = parse_reference(line)
            if len(parsed) < 2:
                continue
                
            ref_authors = parsed[0]
            ref_year = parsed[1]
            
            # Extract first author from reference
            first_ref_author = ref_authors.split(',')[0].split('&')[0].split(' and ')[0].strip()
            first_ref_author_norm = normalize_author(first_ref_author)
            
            # Try different matching strategies
            match_found = False
            if target_author:
                # Exact match
                if first_ref_author_norm == target_author:
                    match_found = True
                # Last name match
                elif first_ref_author_norm.split() and target_author.split():
                    if first_ref_author_norm.split()[-1] == target_author.split()[-1]:
                        match_found = True
                # Corporate author match
                elif any(term in target_author for term in first_ref_author_norm.split()):
                    match_found = True
            
            if match_found and ref_year == year_part:
                return line
                
        return None

    def process_citation(match):
        nonlocal messages, conversion_count
        try:
            original = match.group(0)
            group_content = match.group(1)

            # Skip non-citations
            if not re.search(r'\d{4}[a-z]?', group_content):
                return original

            group_content = re.sub(r'^(e\.g\.,|i\.e\.,)\s*', '', group_content, re.IGNORECASE)
            citations = [c.strip() for c in group_content.split(';')]
            keys = []

            for citation in citations:
                # Skip non-citations
                if not re.search(r',\s*\d{4}[a-z]?$', citation) and not re.search(r'\d{4}[a-z]?\)$', citation):
                    continue
                    
                # Handle special cases
                if re.search(r'Section\s+\d+', citation, re.IGNORECASE):
                    continue
                    
                # Handle LaTeX escaped ampersands in citations
                citation = citation.replace('\\&', '&')
                    
                # Flexible citation patterns
                citation_match = re.match(r'^(.*?[^,])\s*,\s*(\d{4}[a-z]?)$', citation) or \
                                re.match(r'^([^(]+?)\s*\((\d{4}[a-z]?)\)$', citation)
                if not citation_match:
                    continue
                    
                author_part = citation_match.group(1).strip()
                year_part = citation_match.group(2).strip()

                # Handle corporate authors
                if '&' in author_part or ' and ' in author_part:
                    first_author = author_part
                elif 'et al.' in author_part:
                    first_author = author_part.split('et al.')[0].split(',')[0].strip()
                    if ' ' in first_author:
                        first_author = first_author.split()[-1]
                else:
                    authors = re.split(r', | & | and ', author_part)
                    if authors:
                        first_author = authors[0].split(',')[0].strip()
                        if ' ' in first_author:
                            first_author = first_author.split()[-1]
                    else:
                        first_author = ''

                if not first_author:
                    continue

                # Normalize for matching
                first_author_norm = normalize_author(first_author)
                
                reference_line = get_reference_line_by_author_year(input_refs, first_author_norm, year_part)
                if not reference_line:
                    continue

                key = get_reference_key(reference_line, bib_database)
                if not key:
                    continue
                    
                keys.append(key)
                conversion_count += 1

            if keys:
                prefix = 'e.g., ' if 'e.g.' in original.lower() else ''
                return f'({prefix}\\citep{{{",".join(keys)}}})' if prefix else f'\\citep{{{",".join(keys)}}}'
            else:
                return original
        except Exception:
            return match.group(0)

    def process_textual_citation(match):
        nonlocal messages, conversion_count
        try:
            # Handle LaTeX escaped ampersands
            authors_text = match.group(1).replace('\\&', '&').strip()
            year_text = match.group(2)
            
            # Enhanced phrase removal
            authors_text = re.sub(
                r'^(For instance|Similarly|Building upon|For example|In contrast|Additionally|Specifically|'
                r'following|adopting|However|Our findings|further|suggesting|aligns? with|Comparison with|'
                r'In this|Contrary to|While|Finally|This robust test|This robustness test|informed by|'
                r'This result|By replacing|By|UET, introduced by|noindent|This theory, as articulated by|'
                r'as defined by|We adopt the methodology of|Following|However, our results|Our findings|'
                r'Contrary to expectations|),?\s*',
                '', 
                authors_text, 
                flags=re.IGNORECASE
            ).strip()
            
            # Handle special prefixes
            authors_text = re.sub(r'^noindent\s+', '', authors_text, re.IGNORECASE)
            
            # Handle corporate authors
            if '&' in authors_text or ' and ' in authors_text:
                first_author = authors_text
            elif 'et al.' in authors_text:
                first_author = authors_text.split('et al.')[0].split(',')[0].strip()
                if ' ' in first_author:
                    first_author = first_author.split()[-1]
            else:
                authors_split = re.split(r', | & | and ', authors_text)
                if authors_split:
                    first_author = authors_split[0].split(',')[0].strip()
                    if ' ' in first_author:
                        first_author = first_author.split()[-1]
                else:
                    first_author = ''
            
            if not first_author:
                return match.group(0)
            
            # Normalize for matching
            first_author_norm = normalize_author(first_author)
            
            reference_line = get_reference_line_by_author_year(input_refs, first_author_norm, year_text)
            if not reference_line:
                return match.group(0)
            
            key = get_reference_key(reference_line, bib_database)
            if key:
                conversion_count += 1
                return f'\\citet{{{key}}}'
            else:
                return match.group(0)
        except Exception:
            return match.group(0)

    try:
        # Improved textual citation regex
        converted_tex = re.sub(
            r'([A-Z][A-Za-z\s,&]+?(?:\s+et al\.?)?)\s*\((\d{4}[a-z]?)\)',
            process_textual_citation,
            input_tex
        )
        converted_tex = re.sub(r'\(([^)]+)\)', process_citation, converted_tex)
        
        # Add success message
        if conversion_count > 0:
            messages.insert(0, f"✅ Successfully converted {conversion_count} citations")
        else:
            messages.insert(0, "⚠️ No citations were converted. Please check your input formats")
            
        return {"output": converted_tex, "messages": messages}
        
    except Exception as e:
        return {"output": original_tex, "messages": [f"Conversion error: {str(e)}"]}

def main(refs_text, tex_text, bib_text):
    """Main conversion function"""
    try:
        result = apa2tex(refs_text, tex_text, bib_text)
        return (result["output"], json.dumps(result["messages"]))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return (tex_text, json.dumps([f"Critical error: {str(e)}\n{error_trace}"]))
