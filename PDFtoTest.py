import fitz #ref: https://pymupdf.readthedocs.io/en/latest/
import re #ref: https://docs.python.org/3/library/re.html
import json #ref: https://docs.python.org/3/library/json.html
import sys

'''
Intended JSON layout
{
  "1": {
    "instructions": "Directions on set questions",
    "questions": {
      "1": {
        "question": "...",
        "options": {
          "a.": "...",
          "b.": "...",
          "c.": "...",
          "d.": "...",
          "e.": "..."
        },
        "answer": {
          "c": "Explanation..."
        }
      },
      "2": {
        "question": "...",
        "options": {
          "a.": "...",
          "b.": "...",
          "c.": "...",
          "d.": "...",
          "e.": "..."
        },
        "answer": {
          "c": "Explanation..."
        }
      }
    }
  },
  "2": {
    Next question set here
  },
}

'''

pdf_list = [
    "LogicalReasoning",
    "WordAnalogies"
]

def extractText(file):
    doc = fitz.open(file)
    with open(f'{file}Text.md', 'w') as f:
        for page in doc:
            text = page.get_text()
            lines = text.splitlines()
            skip = False
            for i, line in enumerate(lines):
                pattern = re.match(r'^\d+\.\s*[^\d\s]', line)
                if line[-1] == '-':
                    f.write(f"{line[:-1]}")
                    continue
                #if pattern and len(line.strip().split()) > 5:
                if pattern and not lines[i + 1].strip().startswith('a.'):
                    f.write(f"{line} ")
                    continue
                if skip:
                    skip = False
                    continue
                if line == '–QUESTIONS–' or line == '–ANSWERS–' or line == '–NOTES–':
                    skip = True
                    continue
                f.write(f"{line}\n")
            f.write("\n\n")
           
           
#The next step is to manually validate the MD file, as well as extract pictures
#I.e., I'll manually pull the questions and answers at this time into separate MD files, and clean up syntax, separated by 'Sets'
# This actually took quite a bit of editing, and still needs validation...


def pretty(s):
    replacements = {
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2014': '-',  # em dash
        '\u2013': '-',  # en dash
        '\ufb01': 'fi', # 'ﬁ' ligature
        '\ufb02': 'fl', # 'ﬂ' ligature
        '\xa0': ' ',    # non-breaking space
        '\u2026': '...', # ellipsis
    }

    for bad, good in replacements.items():
        s = s.replace(bad, good)

    return s
   
def extractQuestions(file):
    questions = {}
    tally = 1

    with open(file, 'r') as f:
        lines = f.readlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            pattern = re.match(r'(\d+)\.', line)

            if pattern:
                question = re.sub(r'^\d+\.\s*', '', line)
                i += 1
                option = {}
                current_key = None

                while i < len(lines):
                    next_line = lines[i].strip()

                    # Check if next line starts a new option (e.g., "a." or "b)")
                    option_match = re.match(r'^([a-eA-E][\.\)])\s+(.*)', next_line)
                    end_set_match = re.match(r'\ufffd\s*set', next_line, re.IGNORECASE)
                    question_match = re.match(r'^\d+\.', next_line)

                    if question_match:
                        # Next question starts - break option loop
                        break
                    if end_set_match:
                        # end of options - break option loop
                        break
                    if option_match:
                        # New option found
                        current_key = option_match.group(1)
                        option[current_key] = option_match.group(2)
                    else:
                        # Continuation of previous option text
                        if current_key:
                            option[current_key] += ' ' + next_line
                        else:
                            # No current option key: continuation of question text
                            question += ' ' + next_line
                    i += 1

                answer = {}
               
                question = pretty(question)
               
                questions[tally] = blockSetter(question, option, answer)
                tally += 1
            else:
                i += 1

    return questions

def extractSets(file):
    
    sets = {}
    set = 1
    
    with open(file, 'r') as f:
        lines = f.readlines()
        i = 0
        
        question_tally = 1

        while i < len(lines):
            line = lines[i].strip()
            set_match = re.match(r'\ufffd\s*set', line, re.IGNORECASE)
            question_match = re.match(r'^\d+\.', line)
            option_match = re.match(r'^([a-eA-E][\.\)])\s+(.*)', line)
            
            if set_match: # we're in the set
                i += 1
                set_instructions = ''
                current_set = set
                while i < len(lines): # need to get the remaining set instructions
                    next_line = lines[i].strip()
                    question_match = re.match(r'^\d+\.', next_line)
                    
                    if question_match:
                        # found the end of the set instructions
                        break
                    else:
                        set_instructions += ' ' + next_line
                        
                    i += 1
                    sets[current_set] = {'instructions': pretty(set_instructions), 'questions': {}}
                set += 1
                
            elif question_match and (set - 1) in sets:
                current_set = set - 1
                question = re.sub(r'^\d+\.\s*', '', line)
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    option_match = re.match(r'^([a-eA-E][\.\)])\s+(.*)', next_line)
                    question_match = re.match(r'^\d+\.', next_line)
                    set_match = re.match(r'\ufffd\s*set', next_line, re.IGNORECASE)
                    if option_match:
                        # found the end of the question
                        break
                    elif question_match:
                         # quick fail for missing image questions
                         break
                    elif set_match:
                         # quick fail for missing image questions
                         break 
                    else:
                        question += ' ' + next_line
                    
                    i += 1
                    
                sets[current_set]['questions'][question_tally] = {'question': pretty(question), 'options': {}, 'answer':{}}
                question_tally += 1
            
            elif option_match and (set - 1) in sets:
                current_set = set - 1
                options = {}
                option_key = option_match.group(1)
                options[option_key] = pretty(option_match.group(2))     
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    option_match = re.match(r'^([a-eA-E][\.\)])\s+(.*)', next_line)
                    question_match = re.match(r'^\d+\.', next_line)
                    set_match = re.match(r'\ufffd\s*set', next_line, re.IGNORECASE)
                    if option_match:
                        option_key = option_match.group(1)
                        options[option_key] = pretty(option_match.group(2))
                        i += 1
                        continue
                    elif question_match:
                         # quick fail for missing image questions
                         break
                    elif set_match:
                         # quick fail for missing image questions
                         break 
                    options[option_key] += ' ' + pretty(next_line)
                    i += 1
                    
                sets[current_set]['questions'][question_tally - 1]['options'] = options
            else:
                i += 1
                
    return sets

def extractAnswers(file, sets):
    
    with open(file, 'r') as f:
        lines = f.readlines()
        i = 0
        
        question = 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            answer_match = re.match(r'(\d+)\.', line)
            
            if answer_match:
                i += 1                
                answer = re.sub(r'^\d+\.\s*', '', line)
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    set_match = re.match(r'\ufffd\s*set', next_line, re.IGNORECASE)
                    answer_match = re.match(r'(\d+)\.*', next_line)
                    
                    if set_match:
                        break
                    if answer_match:
                        break
                    answer += f" {next_line}"
                    i += 1
                
                key = answer[:2].strip()
                value = answer[2:].strip()

                for set_num, set in sets.items():
                    if question in set['questions']:
                        set['questions'][question]['answer'][key] = pretty(value)
                        break
                
                question += 1
            else:
                i += 1                
        
    return sets
    
def JSONBourne(file, count):
    extractText(f'{file}.pdf')
    sets = extractSets(f'{file}Questions.md')
    extractAnswers(f'{file}Answers.md', sets)
   
    if isinstance(count, str) and count == "all":
        print(json.dumps(sets, indent=2, ensure_ascii=False))
    elif isinstance(count, int):
        print(json.dumps(sets[count], indent=2, ensure_ascii=True))
   
    return sets

if __name__ == "__main__":
    try:
        count = sys.argv[1] if len(sys.argv) > 1 else 'all'
       
        if count != 'all':
            count = int(count)
       
        JSONBourne(pdf_list[0], count)
       
    except ValueError:
        print("Error: count must be an integer or 'all'")
    except Exception as e:
        print(f"Error: {e}")