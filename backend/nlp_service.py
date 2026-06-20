import re
from collections import Counter

try:
    import spacy
    NLP = spacy.blank("en")
except (ImportError, OSError):
    NLP = None

CATEGORY_TERMS = {
    "Polity": {"constitution": 3, "constitutional": 3, "parliament": 3, "court": 2.5, "supreme court": 3, "bill": 2.5, "act": 1.5, "election": 2.5, "rights": 2, "federal": 2.5, "article": 1.5, "governor": 2, "judiciary": 2.5},
    "Governance": {"governance": 3, "ministry": 1.2, "scheme": 1.8, "mission": 1.2, "delivery": 2, "transparency": 2.5, "accountability": 2.5, "welfare": 2, "policy": 1.5, "implementation": 1.8, "public service": 2.5},
    "Economy": {"economy": 3, "economic": 2.5, "gdp": 3, "inflation": 3, "bank": 2, "rbi": 3, "trade": 2.5, "market": 2, "tax": 2.5, "budget": 2.5, "finance": 2, "fiscal": 2.5, "monetary": 2.5, "exports": 2, "investment": 1.8},
    "Environment": {"climate": 3, "forest": 3, "wildlife": 3, "pollution": 3, "renewable": 2.5, "emission": 3, "biodiversity": 3, "conservation": 2.5, "green": 1.5, "wetland": 2.5, "carbon": 2.5, "disaster": 1.7},
    "International Relations": {"diplomatic": 3, "bilateral": 3, "summit": 2.5, "treaty": 3, "global": 1.4, "foreign": 2.5, "united nations": 3, "g20": 3, "brics": 3, "asean": 3, "quad": 3, "border talks": 2.5},
    "Science & Technology": {"space": 3, "isro": 3, "satellite": 3, "quantum": 3, "artificial intelligence": 3, "ai": 2.5, "semiconductor": 3, "biotechnology": 3, "genome": 3, "vaccine": 2.5, "cyber technology": 2.5, "digital technology": 2.2, "science": 0.8, "technology": 0.7, "digital": 0.6, "research": 0.5},
    "Security": {"security": 3, "defence": 3, "border": 2.5, "cyber attack": 3, "terrorism": 3, "insurgency": 3, "maritime": 2.5, "military": 2.5, "police": 2, "surveillance": 1.8},
    "Social Issues": {"health": 2.5, "education": 2.5, "poverty": 3, "gender": 3, "nutrition": 3, "tribal": 2.5, "social justice": 3, "inequality": 2.5, "women": 2, "children": 2, "migration": 2},
    "Agriculture": {"agriculture": 3, "farm": 2.5, "farmer": 2.5, "crop": 3, "irrigation": 3, "msp": 3, "soil": 2.5, "food security": 3, "fertiliser": 2.5, "procurement": 2.2},
    "Ethics": {"ethics": 3, "integrity": 3, "values": 2.5, "probity": 3, "attitude": 2.5, "empathy": 3, "civil service": 2.5, "conflict of interest": 3, "accountability": 1.8},
    "History": {"history": 3, "heritage": 3, "ancient": 3, "archaeological": 3, "freedom": 2.5, "museum": 2.5, "civilisation": 3, "centenary": 2.5, "monument": 2.5, "inscription": 3},
    "Geography": {"monsoon": 3, "river": 2.5, "cyclone": 3, "earthquake": 3, "geography": 3, "urbanisation": 2.5, "landslide": 3, "glacier": 3, "coastal": 2, "watershed": 2.5},
}

CATEGORIES = {category: list(terms) for category, terms in CATEGORY_TERMS.items()}

STOP = set(
    "a an the and or but if in on at to for of with by from as is are was were be been being it its this that these those "
    "into about over after before than has have had will would can could should may india indian new said also under per "
    "cent government state states national year years".split()
)

SCHEME_RE = re.compile(r"\b(?:PM|Pradhan Mantri|National|Atal|Digital|Ayushman|Jal Jeevan|Swachh|Skill India|Mission)\s+[A-Z][A-Za-z0-9& -]{2,60}")
ARTICLE_RE = re.compile(r"\bArticle\s+\d{1,3}[A-Z]?\b", re.I)
COMMITTEE_RE = re.compile(r"\b[A-Z][A-Za-z-]+(?:\s+[A-Z][A-Za-z-]+){0,2}\s+(?:Committee|Commission|Panel)\b")
REPORT_RE = re.compile(r"\b[A-Z][A-Za-z& -]{3,80}\s+(?:Report|Index|Survey|Outlook)\b")
ORG_RE = re.compile(r"\b(?:UN|UNDP|UNEP|UNESCO|WHO|WTO|IMF|World Bank|G20|BRICS|ASEAN|QUAD|RBI|NITI Aayog|IPCC)\b")


def sentences(text):
    try:
        from nltk.tokenize import sent_tokenize
        parsed = sent_tokenize(text)
        if parsed:
            return [s.strip() for s in parsed if len(s.strip()) > 20]
    except (ImportError, LookupError):
        pass
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 20]


def words(text):
    if NLP:
        return [token.text.lower() for token in NLP(text) if token.is_alpha and len(token.text) > 2]
    return re.findall(r"[A-Za-z][A-Za-z&-]{2,}", text.lower())


def unique(values, limit=8):
    seen, result = set(), []
    for value in values:
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" .,:;-")
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def extract_keywords(text, limit=8):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=50)
        scores = vectorizer.fit_transform([text]).toarray()[0]
        terms = vectorizer.get_feature_names_out()
        return [terms[i].title() for i in scores.argsort()[::-1][:limit]]
    except (ImportError, ValueError):
        pass
    counts = Counter(w for w in words(text) if w not in STOP)
    return [word.title() for word, _ in counts.most_common(limit)]


def summarize(text, max_sentences=3):
    items = sentences(text)
    if len(items) <= max_sentences:
        return " ".join(items) or text.strip()
    frequency = Counter(w for w in words(text) if w not in STOP)
    ranked = []
    for index, sentence in enumerate(items):
        tokens = words(sentence)
        score = sum(frequency[token] for token in tokens if token in frequency) / max(len(tokens), 1)
        ranked.append((score, index, sentence))
    chosen = sorted(sorted(ranked, reverse=True)[:max_sentences], key=lambda row: row[1])
    return " ".join(row[2] for row in chosen)


def short_summary(text):
    draft = summarize(text, 2)
    parts = draft.split()
    return " ".join(parts[:100])


def _term_hits(haystack, term):
    pattern = r"\b" + re.escape(term).replace(r"\ ", r"\s+") + r"\b"
    return len(re.findall(pattern, haystack))


def category_scores(text):
    haystack = re.sub(r"\s+", " ", text.lower())
    title_zone = haystack[:220]
    scores = {}
    for category, terms in CATEGORY_TERMS.items():
        score = 0.0
        for term, weight in terms.items():
            hits = _term_hits(haystack, term)
            if not hits:
                continue
            score += hits * weight
            if _term_hits(title_zone, term):
                score += weight * 2.2
        scores[category] = round(score, 3)
    return scores


def classify(text):
    scores = category_scores(text)
    if not scores or max(scores.values()) <= 0:
        return "Polity"
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    # Broad words such as "digital", "technology" and "research" appear in many
    # newspaper pages. Require a clear margin before assigning Science & Technology.
    if ranked[0][0] == "Science & Technology" and len(ranked) > 1 and ranked[0][1] < ranked[1][1] * 1.35:
        return ranked[1][0]
    return ranked[0][0]


def key_facts(text, limit=6):
    facts = []
    for sentence in sentences(text):
        if re.search(r"\b(\d+|crore|lakh|percent|per cent|billion|million|launched|approved|announced|reported)\b", sentence, re.I):
            facts.append(sentence)
    if len(facts) < 3:
        facts.extend(sentences(text)[:limit])
    return unique(facts, limit)


def extract_entities(text):
    return {
        "governmentSchemes": unique(SCHEME_RE.findall(text), 6),
        "constitutionalArticles": unique(ARTICLE_RE.findall(text), 6),
        "committees": unique(COMMITTEE_RE.findall(text), 6),
        "reports": unique(REPORT_RE.findall(text), 6),
        "internationalOrganizations": unique(ORG_RE.findall(text), 8),
    }


def generate_mcqs(title, summary, keywords, category):
    lead = keywords[0] if keywords else title.split()[0]
    second = keywords[1] if len(keywords) > 1 else "implementation"
    return [
        {
            "type": "Statement Based",
            "question": f"With reference to '{title}', consider the following statements: 1. It is relevant to {category}. 2. It has implications for public policy and governance. Which of the statements is/are correct?",
            "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"],
            "answer": "Both 1 and 2",
            "explanation": f"The brief is classified under {category} and connects the event to policy outcomes.",
        },
        {
            "type": "Multiple Statement Analysis",
            "question": f"Which of the following is the most important UPSC keyword in this article?",
            "options": [lead, "Plate tectonics", "Classical dance", "Temperate grasslands"],
            "answer": lead,
            "explanation": f"{lead} is one of the highest-weighted terms extracted from the article.",
        },
        {
            "type": "Match The Following",
            "question": f"Match the issue '{lead}' with the most appropriate syllabus area.",
            "options": [category, "Art and Culture", "World Physical Geography", "Ancient History"],
            "answer": category,
            "explanation": f"The language and context of the article align most strongly with {category}.",
        },
        {
            "type": "Assertion Reason",
            "question": f"Assertion (A): The issue discussed in '{title}' is important for Civil Services preparation. Reason (R): It links a current event with syllabus themes and possible policy questions.",
            "options": ["Both A and R are true and R explains A", "Both A and R are true but R does not explain A", "A is true but R is false", "A is false but R is true"],
            "answer": "Both A and R are true and R explains A",
            "explanation": "Current affairs become exam-relevant when they can be tied to static syllabus concepts and policy debates.",
        },
        {
            "type": "Application",
            "question": f"Which pair best captures the analytical frame for this article?",
            "options": [f"{lead} - {category}", f"{second} - Sports", "Dynasty - Numismatics", "Ocean trench - Ethics"],
            "answer": f"{lead} - {category}",
            "explanation": f"The article uses {lead} as a core term and is categorized under {category}.",
        },
    ]


def generate_mains(title, category, keywords):
    lead = keywords[0] if keywords else "the issue"
    paper = {
        "Polity": "GS-II", "Governance": "GS-II", "International Relations": "GS-II",
        "Economy": "GS-III", "Environment": "GS-III", "Science & Technology": "GS-III",
        "Security": "GS-III", "Agriculture": "GS-III", "Ethics": "GS-IV",
        "History": "GS-I", "Geography": "GS-I", "Social Issues": "GS-I",
    }.get(category, "GS-II")
    return [
        {
            "paper": paper,
            "directive": "Discuss",
            "wordLimit": 150,
            "question": f"Discuss the significance of {lead} in the context of {title}.",
            "modelAnswerPoints": ["Define the issue briefly", "Connect it with the syllabus theme", "Mention institutional or policy implications", "Conclude with a balanced way forward"],
        },
        {
            "paper": paper,
            "directive": "Critically Examine",
            "wordLimit": 250,
            "question": f"Critically examine the opportunities and challenges arising from {title}.",
            "modelAnswerPoints": ["Present benefits", "Identify implementation concerns", "Use examples or data points from the brief", "Suggest accountable and inclusive reforms"],
        },
        {
            "paper": "GS-IV" if category == "Ethics" else paper,
            "directive": "Analyze",
            "wordLimit": 150,
            "question": f"Analyze how administrators should respond to the policy concerns reflected in {title}.",
            "modelAnswerPoints": ["Stakeholder mapping", "Evidence-based decision-making", "Transparency and public communication", "Outcome monitoring"],
        },
    ]


def related_pyqs(category, keywords):
    lead = keywords[0] if keywords else category
    bank = {
        "Environment": [("2023", "Discuss the implications of climate change for India's development pathway."), ("2021", "Examine the role of biodiversity conservation in sustainable development.")],
        "Economy": [("2023", "Explain the factors responsible for inflation and its impact on vulnerable groups."), ("2020", "Discuss the role of monetary policy in ensuring macroeconomic stability.")],
        "Polity": [("2023", "Examine the significance of constitutional morality in Indian democracy."), ("2018", "Discuss the importance of parliamentary oversight in governance.")],
        "Governance": [("2022", "E-governance is not only about technology but also about process reform. Discuss.")],
        "International Relations": [("2023", "Analyze India's role in emerging global groupings.")],
        "Science & Technology": [("2021", "What are the applications and concerns associated with emerging digital technologies?")],
    }
    items = bank.get(category, [("2022", f"Discuss the relevance of {lead} for India's development and governance.")])
    return [{"year": year, "question": question, "answerHint": f"Link {lead} with current developments, static concepts and a balanced conclusion."} for year, question in items[:3]]


def analyze(title, content):
    text = f"{title}. {content}"
    category = classify(text)
    keywords = extract_keywords(text)
    summary = short_summary(content)
    detailed = summarize(content, 5)
    entities = extract_entities(text)
    mcqs = generate_mcqs(title, summary, keywords, category)
    mains = generate_mains(title, category, keywords)
    return {
        "summary": summary,
        "shortSummary": summary,
        "detailedSummary": detailed,
        "keyFacts": key_facts(content),
        "keywords": keywords,
        "importantTerms": keywords[:6],
        "category": category,
        **entities,
        "mcqs": mcqs,
        "shortAnswerQuestions": [f"Explain the significance of {keywords[0] if keywords else title} in this development."],
        "practiceQuestions": [item["question"] for item in mains],
        "mainsQuestions": mains,
        "pyqs": related_pyqs(category, keywords),
    }
