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
        from bibtexparser.bibdatabase import BibDatabase
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = bibtexparser.loads(bib_text, parser=parser)
    except Exception as e:
        messages.append(f"Error parsing BibTeX file: {str(e)}")
        return {"output": original_tex, "messages": messages}

    def process_citation(match):
        nonlocal messages, conversion_count
        try:
            original = match.group(0)
            group_content = match.group(1)

            # Skip processing if content doesn't look like a citation
            if not re.search(r'\d{4}[a-z]?', group_content):
                return original

            group_content = re.sub(r'^(e\.g\.,|i\.e\.,)\s*', '', group_content, flags=re.IGNORECASE)
            citations = [c.strip() for c in group_content.split(';')]
            keys = []
            valid = True
            processed_citations = []

            for citation in citations:
                # Skip if doesn't look like a citation (no year pattern)
                if not re.search(r',\s*\d{4}[a-z]?$', citation):
                    processed_citations.append(citation)
                    continue
                    
                citation = re.sub(r'^(e\.g\.,|i\.e\.,)\s*', '', citation, flags=re.IGNORECASE).strip()
                # Update regex to handle escaped ampersands
                citation_match = re.match(r'^(.*?),\s*(\d{4}[a-z]?)$', citation)
                if not citation_match:
                    processed_citations.append(citation)
                    continue
                    
                author_part, year_part = citation_match.groups()

                # Handle both escaped and unescaped ampersands
                if 'et al.' in author_part:
                    # Remove escaping for comparison
                    first_author = author_part.split('et al.')[0].split(',')[0].strip().replace('\\&', '&')
                else:
                    # Split on both & and \&
                    authors = re.split(r', | & | \\& | and ', author_part)
                    first_author = authors[0].split(',')[0].strip().replace('\\&', '&') if authors and len(authors) > 0 else ''
                    if not first_author:
                        processed_citations.append(citation)
                        continue

                reference_line = get_reference_line_by_author_year(input_refs, first_author, year_part)
                if not reference_line:
                    messages.append(f"Reference not found for {citation}")
                    processed_citations.append(citation)
                    continue

                key = get_reference_key(reference_line, bib_database)
                if not key:
                    messages.append(f"Key not found for {citation}")
                    processed_citations.append(citation)
                    continue
                    
                keys.append(key)
                processed_citations.append(None)  # Mark as successfully processed

            # If we have at least one valid key
            if keys:
                conversion_count += len(keys)
                prefix = 'e.g., ' if 'e.g.' in original.lower() else ''
                return f'({prefix}\\citep{{{",".join(keys)}}})'
            else:
                # Return original if no keys found
                return original
                
        except Exception as e:
            return match.group(0)

    def process_textual_citation(match):
        nonlocal messages, conversion_count
        try:
            authors_text = match.group(1).strip()
            year_text = match.group(2)
            
            # Handle both escaped and unescaped ampersands
            if 'et al.' in authors_text:
                # Remove escaping for comparison
                first_author = authors_text.split('et al.')[0].split(',')[0].strip().replace('\\&', '&')
            else:
                # Split on both & and \&
                authors_split = re.split(r', | & | \\& | and ', authors_text)
                first_author = authors_split[0].split(',')[0].strip().replace('\\&', '&') if authors_split and len(authors_split) > 0 else ''
            
            reference_line = get_reference_line_by_author_year(input_refs, first_author, year_text)
            if not reference_line:
                messages.append(f"Textual reference not found for {authors_text} ({year_text})")
                return match.group(0)
            
            key = get_reference_key(reference_line, bib_database)
            if key:
                conversion_count += 1
                # Preserve original escaping in output
                output = f'\\citet{{{key}}}'
                # Restore ampersand escaping if it existed in original
                if '\\&' in authors_text:
                    output = output.replace(' & ', ' \\& ')
                return output
            else:
                messages.append(f"Key not found for textual citation: {authors_text} ({year_text})")
                return match.group(0)
                
        except Exception as e:
            return match.group(0)

    try:
        # First handle textual citations (Author (Year))
        converted_tex = re.sub(
            r'(\b[\w\s,&]+?(?:\s+et al\.?)?)\s+\((\d{4}[a-z]?)\)',
            process_textual_citation,
            input_tex
        )
        # Then handle parenthetical citations ((Author, Year; Author2, Year))
        converted_tex = re.sub(r'\(([^)]+)\)', process_citation, converted_tex)
        
        # Preserve existing ampersand escaping in the rest of the document
        converted_tex = converted_tex.replace(' & ', ' \\& ')
        
        # Add success message if conversions occurred
        if conversion_count > 0:
            support_message = (
                f"✅ Successfully converted {conversion_count} citations. "
                "If you find this ad-free website helpful, please consider "
                "supporting us at <a href='https://coff.ee/orangemeowmeow' "
                "target='_blank'>coff.ee/orangemeowmeow</a>! ❤️"
            )
            messages.insert(0, support_message)
        else:
            messages.insert(0, "⚠️ No citations were converted. Please check your input formats")
            
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

main = main
