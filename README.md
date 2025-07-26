# PDFtoTEST.py
Work in progress -- Convert PDF test booklets/sets into JSON data in order to feed to quiz generators.

Test subject used was the '501 CHALLENGING LOGIC AND REASONING PROBLEMS - ISBN 1-57685-534-1

The point of this program was to help with self studying, I have yet to incorporate feeding the test set into a quiz generator, though I was going to build my own with Streamlit.

To run:

Generate first set questions:
py ./PDFtoTest.py 1 >> test_set1.json

Generate all sets:
py ./PDFtoTest.py >> test_sets.json
