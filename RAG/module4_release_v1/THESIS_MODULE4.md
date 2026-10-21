# RAG-assisted σύντηξη εξωτερικής λεξικής τεκμηρίωσης

## Στόχος της επέκτασης

Το Module 4 εξετάζει αν η εξωτερική λεξική γνώση μπορεί να λειτουργήσει ως συμπληρωματική πηγή χαρακτηριστικών για την ανίχνευση hallucination στο SHROOM. Αφετηρία είναι το E3, δηλαδή το επιλεγμένο development baseline που συνδυάζει έξι χαρακτηριστικά Natural Language Inference (NLI) και οκτώ χαρακτηριστικά σημασιολογικής ομοιότητας. Το E3 χρησιμοποιεί Random Forest και αξιολογείται με πέντε προκαθορισμένα outer folds. Η επέκταση E5 δεν αντικαθιστά αυτόν τον κορμό. Προσθέτει επτά χαρακτηριστικά που προκύπτουν από εξωτερική λεξική τεκμηρίωση και εξετάζει την επίδρασή τους στην ίδια ακριβώς development-only out-of-fold διαδικασία.

Το ερευνητικό ερώτημα είναι περιορισμένο: μπορεί ένας frozen, label-free retrieval branch να προσφέρει χρήσιμη πληροφορία πέρα από τα χαρακτηριστικά του E3; Δεν εξετάζεται παραγωγή απαντήσεων από LLM, ούτε χρήση Gemini. Επίσης, δεν γίνεται ισχυρισμός ότι το πείραμα αποτελεί ανεξάρτητη αξιολόγηση. Το `tgt` χρησιμοποιείται μετά το κλείδωμα των retrieved candidates για σύγκριση της λεξικής τεκμηρίωσης με τη reference. Για αυτόν τον λόγο, η διαδικασία χαρακτηρίζεται reference-assisted.

## Εξωτερική λεξική τεκμηρίωση και retrieval

Ο αρχικός σχεδιασμός προέβλεπε WordNet 3.1 και English Wiktionary. Μετά από αποτυχημένες ασφαλείς προσπάθειες απόκτησης του WordNet και πριν από τη νέα feature inference, η continuation περιορίστηκε ρητά στο English Wiktionary. Η αλλαγή αυτή καταγράφηκε ως protocol deviation και δεν παρουσιάζεται ως αμετάβλητος αρχικός σχεδιασμός. Η τελική snapshot περιείχε 462 μοναδικές λεξικές σημασίες για 188 από τους 206 κανονικοποιημένους DM όρους. Για 18 όρους δεν βρέθηκε διαθέσιμη σημασία, ενώ δεν υπήρξε logical source failure στην αποδεκτή acquisition.

Για κάθε DM παράδειγμα, το query σχηματίστηκε αποκλειστικά από τον όρο και το `src`. Το `tgt`, τα labels, οι probabilities και οι προηγούμενες προβλέψεις δεν χρησιμοποιήθηκαν στο retrieval ή στην ταξινόμηση των candidates. Το MPNet `sentence-transformers/all-mpnet-base-v2` κωδικοποίησε το query και τα κείμενα των υποψήφιων σημασιών. Η κατάταξη βασίστηκε σε cosine similarity, με σταθερό `top_k=5` και deterministic tie-breaking. Στα MT και PG παραδείγματα δεν εφαρμόστηκε λεξικό retrieval και χρησιμοποιήθηκε η προκαθορισμένη πολιτική επτά μηδενικών χαρακτηριστικών.

Μετά το κλείδωμα της ordered top-five λίστας επιτράπηκε η σύγκριση με το `tgt`. Τα επτά χαρακτηριστικά ήταν: διαθεσιμότητα evidence, αριθμός διαθέσιμων σημασιών, cosine του πρώτου retrieved candidate με το query, μέγιστο cosine definition–`tgt`, μέγιστη entailment probability, μέγιστη contradiction probability και μέγιστο lexical token-set overlap. Για τα NLI χαρακτηριστικά χρησιμοποιήθηκε DeBERTa-large-MNLI με premise τη candidate definition και hypothesis το `tgt`. Συνολικά, το frozen feature artifact είχε 561 γραμμές, μία identity στήλη και επτά numeric features. Evidence υπήρχε σε 193/561 γραμμές, ενώ 350/561 MT/PG γραμμές ακολούθησαν την πολιτική μηδενικών.

## Development-only OOF αξιολόγηση

Η αξιολόγηση συνέκρινε μία μόνο frozen E5 configuration με το E3 στις ίδιες 561 γραμμές και στα ίδια πέντε folds. Το E3 χρησιμοποίησε τα 14 αρχικά χαρακτηριστικά και το E5 τα ίδια 14 μαζί με τα επτά RAG χαρακτηριστικά. Και στις δύο περιπτώσεις χρησιμοποιήθηκε η ίδια frozen διαμόρφωση `RandomForestRegressor` με 500 δέντρα και `random_state=42`. Δεν έγινε tuning, ablation ή επιλογή δεύτερου retrieval configuration μετά την εξέταση των αποτελεσμάτων.

Ο ακόλουθος πίνακας συνοψίζει τα συνολικά OOF αποτελέσματα που αναφέρονται στο verified Schannel continuation report.

| Μοντέλο | Accuracy | Spearman |
|---|---:|---:|
| E3 NLI + similarity | 445/561 (79,3226%) | 0,7390395613 |
| E5 RAG-assisted fusion | 446/561 (79,5009%) | 0,7421719692 |

Η E5 διόρθωσε 5/561 περιπτώσεις στις οποίες η E3 είχε σφάλμα, αλλά εισήγαγε 4/561 νέα σφάλματα. Το καθαρό κέρδος ήταν επομένως +1/561 σωστή binary prediction, δηλαδή περίπου +0,18 ποσοστιαίες μονάδες Accuracy. Η προκαθορισμένη score-based απόφαση της συγκεκριμένης development σύγκρισης ήταν `E5_RAG_IMPROVES_DEVELOPMENT_SCORE`, επειδή η Accuracy ήταν αριθμητικά μεγαλύτερη. Ωστόσο, το exact McNemar test είχε `p=1,0` και το αναφερόμενο paired bootstrap 95% interval για τη διαφορά Accuracy ήταν από −0,0089126560 έως 0,0124777184. Εφόσον το διάστημα περιλαμβάνει το μηδέν, η παρατηρούμενη διαφορά δεν τεκμηριώνει σταθερή υπεροχή ή αξιόπιστη γενίκευση.

Η ανάλυση ανά task δείχνει επίσης ότι η μεταβολή δεν ήταν ομοιόμορφη.

| Task | E3 Accuracy | E5 Accuracy | E3 Spearman | E5 Spearman |
|---|---:|---:|---:|---:|
| DM | 155/211 (73,4597%) | 157/211 (74,4076%) | 0,6400104693 | 0,6427316315 |
| MT | 185/216 (85,6481%) | 185/216 (85,6481%) | 0,7960447809 | 0,7972150618 |
| PG | 105/134 (78,3582%) | 104/134 (77,6119%) | 0,6961810929 | 0,6949901408 |

Η βελτίωση της DM Accuracy συνοδεύτηκε από αμετάβλητη MT Accuracy και μικρότερη PG Accuracy. Αν και τα RAG features είναι μηδενικά στις MT/PG γραμμές, αυτό δεν σημαίνει ότι ο νέος συνδυαστικός classifier θα δώσει υποχρεωτικά τις ίδιες προβλέψεις με το E3. Η εκπαίδευση του Random Forest πάνω σε διαφορετικό συνολικό feature space μπορεί να αλλάξει τις learned partitions και, συνεπώς, τη συμπεριφορά ακόμη και σε γραμμές όπου τα πρόσθετα features είναι μηδενικά.

## Exact-overlap audit και pinned replay

Επειδή οι candidate definitions συγκρίνονται με το `tgt`, έγινε ξεχωριστός exact-overlap έλεγχος. Εντοπίστηκαν 18/561 γραμμές στις οποίες κάποια top-five candidate definition ήταν ακριβώς ίδια με το `tgt` μετά από Unicode normalization, case folding και whitespace normalization. Στις 18 αυτές γραμμές, E3 και E5 είχαν και τα δύο 13/18 Accuracy, χωρίς καμία διόρθωση ή νέα αστοχία. Μετά την αφαίρεσή τους μόνο από τη διαγνωστική μέτρηση, η E3 είχε 432/543 και η E5 433/543 σωστές προβλέψεις. Και οι πέντε διορθώσεις και οι τέσσερις νέες αστοχίες προήλθαν από non-exact γραμμές.

Η παραπάνω αφαίρεση είναι diagnostic subset analysis. Δεν σημαίνει ότι τα μοντέλα επανεκπαιδεύτηκαν χωρίς τις exact-overlap γραμμές. Επιπλέον, η απουσία exact normalized match δεν αποδεικνύει απουσία κάθε μορφής contamination ή source/reference concordance. Παραφράσεις, κοντινές λεξικές διατυπώσεις και κοινή προέλευση της reference και της εξωτερικής πηγής μπορούν να δημιουργούν overlap που δεν ανιχνεύεται με την ακριβή σύγκριση.

Μετά την ολοκλήρωση του πειράματος, διαπιστώθηκε ότι οι παλαιοί feature και overlap builders φόρτωναν MPNet χωρίς να περνούν ρητά την intended revision, παρότι χρησιμοποιούσαν `local_files_only=True`. Τα διαθέσιμα ιστορικά στοιχεία δεν συνέδεαν την τότε εκτέλεση με συγκεκριμένο resolved snapshot. Για αυτό η ιστορική κατάσταση καταγράφηκε ως `HISTORICAL_REVISION_UNPROVEN` και όχι ως επιβεβαιωμένο match ή mismatch.

Ακολούθησε μία περιορισμένη offline replay με ρητά pinned MPNet και NLI revisions, process-local network guard και καταγραφή των model-file hashes. Η feature generation παρήγαγε ξανά 561 γραμμές με SHA-256 `708483b831430d876135d1484ad841bf6ba0d9c9a2d0a5f22df6280535fe3160`. Το overlap audit παρήγαγε 561 γραμμές και 18 exact-overlap rows με SHA-256 `0fab92f6907da36ae1be609d26230f8b7db054b42bff1f02b578b8719bba714a`. Και τα δύο outputs ήταν byte-identical με τα accepted artifacts. Αυτό τεκμηριώνει σημερινή artifact reproducibility με τα συγκεκριμένα pins. Δεν δημιουργεί αναδρομική απόδειξη για την ιστορική επιλογή snapshot.

## Περιορισμοί και συμπέρασμα

Η μελέτη περιορίζεται σε 561 development rows και εφαρμόζει lexical RAG μόνο στις 211 DM περιπτώσεις. Δεν έγινε ανεξάρτητη holdout αξιολόγηση ούτε πρόσβαση στο official test. Το `tgt` συμμετέχει στη δημιουργία των reference-assisted features, άρα το αποτέλεσμα δεν ισοδυναμεί με deployment setting όπου η σωστή reference δεν είναι διαθέσιμη. Η English-Wiktionary-only επιλογή είναι καταγεγραμμένη απόκλιση από τον αρχικό σχεδιασμό, ενώ το ιστορικό label-exposure incident και το background hub-resolution incident παραμένουν επίσης μέρος του επιστημονικού αρχείου.

Συνολικά, το Module 4 δείχνει ότι ένα μικρό external lexical branch μπορεί να ενσωματωθεί χωρίς να αλλάξει ο βασικός evaluation protocol και ότι τα accepted feature artifacts είναι αναπαραγώγιμα υπό ρητά pinned offline conditions. Η αριθμητική μεταβολή από 445/561 σε 446/561 είναι θετική αλλά πολύ μικρή, και η αβεβαιότητά της περιλαμβάνει μηδενική διαφορά. Συνεπώς, το αποτέλεσμα αντιμετωπίζεται ως τεκμηριωμένη development-only ένδειξη και όχι ως απόδειξη βελτίωσης του τελικού benchmark. Δεν δικαιολογεί αυτόματη προαγωγή του E5 ούτε αλλαγή της προηγούμενης επιλογής του E3 χωρίς νέα, ανεξάρτητη και προκαθορισμένη επιβεβαίωση.

## Σημείωση τεκμηρίωσης

Οι αριθμοί των δύο πινάκων και των uncertainty diagnostics προέρχονται από το `RAG/results/rag_module4/continuation_v1/schannel_run_v1/SCHANNEL_CONTINUATION_FINAL_REPORT.md` και το αντίστοιχο `SCHANNEL_STATE.json`. Τα στοιχεία του pinned replay προέρχονται από το `PINNED_REPLAY_REPORT.md`, το `PRE_RUN_MANIFEST.json` και το `RUNTIME_PROVENANCE_MANIFEST.json` στον φάκελο `replay_20260830T181436Z`. Δεν υπολογίστηκαν νέα πειραματικά metrics για το παρόν προσχέδιο.
