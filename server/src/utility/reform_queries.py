from typing import List, Dict
from pydantic import BaseModel
from .word_maps import load_word_maps

word_maps = load_word_maps()

author_keywords = {"author", "authors", "writer", "writers", "novelist", "novelists", "writtenby"}
publisher_keywords = {"publisher", "publishers", "publishedby", "published", "publishing"}
common_author_publisher_keywords = {"by", "of", "from"}
edition_keywords = {"edition", "editions", "version", "versions"}
category_keywords = {"category", "categories", "genre", "genres", "tag", "tags", "to", "on", "for" }
edition_mapping = {
    ("first", "1", "1st", "1.0"): "1st",
    ("second", "2", "2nd", "2.0"): "2nd",
    ("third", "3", "3rd", "3.0"): "3rd",
    ("fourth", "4", "4th", "4.0"): "4th",
    ("fifth", "5", "5th", "5.0"): "5th",
    ("sixth", "6", "6th", "6.0"): "6th",
    ("seventh", "7", "7th", "7.0"): "7th",
    ("eighth", "8", "8th", "8.0"): "8th",
    ("ninth", "9", "9th", "9.0"): "9th",
    ("tenth", "10", "10th", "10.0"): "10th"
}

stop_words = {
    "the", "is", "in", "and", "that", "this",
    "suggest", "suggestion", "suggestions", "search", "find",
    "recommend", "recommendation", "recommendations", "some", "all", "few", "give", "me",
    "show", "list", "down", "read", "reads", "reading", "complete"
}

keywords = {
    "novel", "book", "books", "literature",
    "author", "authors", "publisher", "publishers",
    "tag", "tags", "category", "categories", "genre", "genres",
    "writer", "writers", "novelist", "novelists", "writtenby",
    "related", "about"
}

class KeyWordSet(BaseModel):
    data: Dict[str, List[str]]

class KeyWords(BaseModel):
    keywords: List[KeyWordSet]

def remove_special_characters(query: str) -> str:
    return ''.join(e for e in query if e.isalnum() or e.isspace())

def all_lowercase(query: str) -> str:
    return query.lower()

def normalize_spacing(query: str) -> str:
    return query.replace("-", " ")

def get_tokens(query: str) -> List[str]:
    return [t for t in query.split() if t]

def singular(word: str) -> str:
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word

def normalize_edition(token: str) -> str:
    for keys, value in edition_mapping.items():
        if token in keys:
            return value
    return ""

def capture_entity(tokens: List[str], start: int):
    res = []
    i = start
    while i < len(tokens):
        if tokens[i] in author_keywords or tokens[i] in publisher_keywords or tokens[i] in edition_keywords or tokens[i] in common_author_publisher_keywords or tokens[i] in category_keywords or tokens[i] in {"related", "about"}:
            break
        res.append(tokens[i])
        i += 1
    return " ".join(res).strip(), i - start

# --- fallback name detection ---
def is_name_token(token: str) -> bool:
    return token.isalpha() and len(token) > 2 and token not in stop_words

def extract_possible_authors(tokens: List[str]) -> List[str]:
    names = []
    current = []

    for token in tokens:
        if is_name_token(token):
            current.append(token)
        else:
            if len(current) >= 2:
                names.append(" ".join(current))
            current = []

    if len(current) >= 2:
        names.append(" ".join(current))

    return names

def key_query_words(tokens: List[str]) -> Dict[str, List[str]]:
    result = {
        "author": [],
        "publisher": [],
        "edition": [],
        "category": [],
        "tag": []
    }

    i = 0
    n = len(tokens)

    while i < n:
        token = tokens[i]

        # ---- AUTHOR ----
        if token in author_keywords:
            val, jump = capture_entity(tokens, i + 1)
            if val:
                result["author"].append(val)
                i += jump + 1
                continue

        # ---- PUBLISHER ----
        elif token in publisher_keywords:
            val, jump = capture_entity(tokens, i + 1)
            if val:
                result["publisher"].append(val)
                i += jump + 1
                continue

        # ---- AMBIGUOUS ----
        elif token in common_author_publisher_keywords:
            val, jump = capture_entity(tokens, i + 1)
            if val:
                # keep both as candidates
                result["author"].append(val)
                result["publisher"].append(val)
                i += jump + 1
                continue

        elif token in category_keywords:
            val, jump = capture_entity(tokens, i + 1)
            if val:
                result["category"].append(val)
                result["tag"].append(val)
                if val in word_maps:
                    result["category"].extend(word_maps[val])
                    result["tag"].extend(word_maps[val])
                i += jump + 1
                continue

        elif token in {"related", "about"}:
            # Forward capture: "related to X" or "about X"
            start_idx = i + 1
            if i + 1 < n and tokens[i + 1] == "to":
                start_idx = i + 2
                
            val, jump = capture_entity(tokens, start_idx)
            if val:
                result["category"].append(val)
                result["tag"].append(val)
                if val in word_maps:
                    result["category"].extend(word_maps[val])
                    result["tag"].extend(word_maps[val])
                i = start_idx + jump
                continue
                
            # Backward capture for "X related" 
            if token == "related" and i > 0:
                back_tokens = []
                j = i - 1
                while j >= 0 and len(back_tokens) < 4:
                    t_b = tokens[j]
                    if t_b in stop_words or t_b in keywords or t_b in common_author_publisher_keywords or t_b in category_keywords:
                        break
                    back_tokens.insert(0, t_b)
                    j -= 1
                
                bval = " ".join(back_tokens).strip()
                if bval:
                    result["category"].append(bval)
                    result["tag"].append(bval)
                    if bval in word_maps:
                        result["category"].extend(word_maps[bval])
                        result["tag"].extend(word_maps[bval])
            
            i += 1
            continue

        # ---- EDITION ----
        elif token in edition_keywords:
            if i + 1 < n:
                ed = normalize_edition(tokens[i + 1])
                if ed:
                    result["edition"].append(ed)
                    i += 2
                    continue

        # ---- DIRECT EDITION ----
        else:
            ed = normalize_edition(token)
            if ed:
                result["edition"].append(ed)
                i += 1
                continue

        i += 1

    # ---- FALLBACK: MULTIPLE AUTHORS ----
    if not result["author"]:
        possible_authors = extract_possible_authors(tokens)
        result["author"].extend(possible_authors)

    return result

def clean_tokens(tokens: List[str]) -> List[str]:
    res = []
    n = len(tokens)
    for i in range(n):
        t = tokens[i]
        if t in stop_words:
            continue
        if t in keywords:
            continue
        if t in common_author_publisher_keywords:
            continue
            
        sing_t = singular(t)
        res.append(sing_t)
        
        # Check single token
        if sing_t in word_maps:
            res.extend(word_maps[sing_t])
            
        # Check bigram (current and next token)
        if i < n - 1:
            next_t = singular(tokens[i+1])
            bigram = f"{sing_t} {next_t}"
            if bigram in word_maps:
                res.extend(word_maps[bigram])
                
    return res

def join_variants(tokens: List[str]) -> List[str]:
    if len(tokens) > 6:
        return [" ".join(tokens)]
    results = set()
    n = len(tokens)
    for i in range(n):
        for j in range(i + 1, min(i + 4, n + 1)):
            combined = tokens[:i] + ["".join(tokens[i:j])] + tokens[j:]
            results.add(" ".join(combined))
    return list(results)

def _try_split_on_keywords(query: str) -> str:
    """Try to split concatenated query on common keywords like 'on', 'by', 'of'"""
    # Common split words that often appear between meaningful parts
    split_words = ["on", "by", "of", "from", "in", "at", "the", "to", "for"]
    
    for word in split_words:
        if word in query:
            # Replace keyword with space
            query = query.replace(word, f" {word} ")
    
    # Also try to split on common keywords at start
    for keyword in ["book", "books", "novel", "novels", "author", "authors"]:
        if query.startswith(keyword) and len(query) > len(keyword):
            # Check if something follows immediately
            remainder = query[len(keyword):]
            if remainder and not remainder[0].isspace():
                query = keyword + " " + remainder
    
    return query

def reformulate_query(query: str):
    query = all_lowercase(query)
    query = normalize_spacing(query)
    query = remove_special_characters(query)

    if " " not in query:
        query = _try_split_on_keywords(query)
    tokens = get_tokens(query)

    keyword_query = key_query_words(tokens)

    cleaned_tokens = clean_tokens(tokens)

    cleaned_query = " ".join(cleaned_tokens)

    # variants = join_variants(cleaned_tokens)
    # if cleaned_tokens:
    #     variants.append("".join(cleaned_tokens))

    return keyword_query, cleaned_query