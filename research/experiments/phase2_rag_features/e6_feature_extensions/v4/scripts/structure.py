"""Predetermined Unicode tokenization and literal structural mismatches; no labels."""
import re,unicodedata
TOKEN_PATTERN=r"[^\W_]+(?:'[^\W_]+)*"
NUMBER_PATTERN=r"(?<![\w.,])(?P<number>[+-]?\d+(?:[.,]\d+)*)(?:[ \t]*(?P<percent>%))?(?!\w)"
NEGATION=['no','not','never','neither','nor','nobody','nothing','nowhere','without','cannot',
          "can't","won't","isn't","aren't","wasn't","weren't","don't","doesn't","didn't",
          "hasn't","haven't","hadn't","shouldn't","wouldn't","couldn't","mustn't"]
NEGATION_SUFFIX="n't"
NAMES=['structure_length_ratio','structure_number_presence_mismatch','structure_number_set_mismatch','structure_negation_mismatch']
SPEC={'normalization':'Unicode NFC, casefold, U+2018/U+2019 apostrophes -> ASCII apostrophe; structural features only',
      'token_regex':TOKEN_PATTERN,'regex_flags':'re.UNICODE','number_regex':NUMBER_PATTERN,
      'number_normalization':'Preserve sign, digit spelling, leading/trailing zeros and percent. A single comma separator becomes dot only with 1 or 2 trailing decimal digits. Ambiguous 3+ comma digits or multiple separators are retained verbatim. Whitespace before percent is syntax, excluded from the extracted value.',
      'negation_lexicon':NEGATION,'negation_suffix':NEGATION_SUFFIX,
      'not_supported':'Spelled-out numbers, fractions, scientific notation and thousands-format interpretation are not resolved; sets ignore repetition and order. Negation flags presence, not scope. No lemmatization or parser.',
      'empty_ratio':'both zero -> 1.0; exactly one zero -> 0.0'}
def normalize(s):return unicodedata.normalize('NFC',s).casefold().replace('\u2018',"'").replace('\u2019',"'")
def tokens(s):return re.findall(TOKEN_PATTERN,normalize(s),flags=re.UNICODE)
def numbers(s):
    found=[]
    for m in re.finditer(NUMBER_PATTERN,normalize(s),flags=re.UNICODE):
        n=m['number']
        if n.count(',')==1 and '.' not in n and len(n.split(',')[1]) in [1,2]:n=n.replace(',','.')
        found.append(n+('%' if m['percent'] else ''))
    return set(found)
def negated(s):return any(t in NEGATION or t.endswith(NEGATION_SUFFIX) for t in tokens(s))
def features(reference,hyp):
    a,b=tokens(reference),tokens(hyp);na,nb=numbers(reference),numbers(hyp)
    ratio=min(len(a),len(b))/max(len(a),len(b)) if a or b else 1.
    values=[ratio,int(bool(na)!=bool(nb)),int(na!=nb),int(negated(reference)!=negated(hyp))]
    return dict(zip(NAMES,values))
def contracts():
    assert features('','')[NAMES[0]]==1 and features('word','')[NAMES[0]]==0
    assert tokens("DON’T naïve Ελληνικά １２")==["don't",'naïve','ελληνικά','１２']
    assert features('There are 12 apples.','There are 13 apples.')[NAMES[2]]==1
    assert features('There are apples.','There are 13 apples.')[NAMES[1]]==1
    assert numbers('12,5% and 0,25')==numbers('12.5 % and 0.25')
    assert numbers('1,000')!=numbers('1.000') and numbers('10')!=numbers('10%')
    assert features('The train is running.','The train is not running.')[NAMES[3]]==1
    assert not negated('notable nobodyish') and negated("shouldn't") and negated("ca n't") and negated("isn’t")
    assert all(negated(t) for t in NEGATION)
    assert features('No apples.','No apples.')[NAMES[3]]==0
    return 'PASS'
